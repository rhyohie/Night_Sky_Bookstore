local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local bookEvent = ReplicatedStorage:WaitForChild("BookEvent")
local getBooks = ReplicatedStorage:WaitForChild("GetBooks")
local player = Players.LocalPlayer

local UserInputService = game:GetService("UserInputService")

-- Hide the cursor immediately when the player spawns!
UserInputService.MouseIconEnabled = false 

-- Create our own invisible button to control the mouse lock
local mouseUnlocker = Instance.new("TextButton")
mouseUnlocker.Size = UDim2.new(0, 0, 0, 0)
mouseUnlocker.Text = ""
mouseUnlocker.BackgroundTransparency = 1
mouseUnlocker.Modal = true

-- === UI HIERARCHY ===
local mainAppFrame = script.Parent
local UIHelper = require(mainAppFrame:WaitForChild("BookstoreUIHelper")) 

local bookGrid = mainAppFrame:WaitForChild("BookGrid")
local template = bookGrid:WaitForChild("BookTemplate")
local closeButton = mainAppFrame:WaitForChild("CloseButton")

local actionBar = mainAppFrame:WaitForChild("ActionBar")
local createBtn = actionBar:WaitForChild("CreateButton")
local updateBtn = actionBar:WaitForChild("UpdateButton")
local deleteBtn = actionBar:WaitForChild("DeleteButton")

local createMenu = mainAppFrame:WaitForChild("CreateBookMenu")
local closeMenuBtn = createMenu:WaitForChild("CloseMenuBtn")
local submitBtn = createMenu:WaitForChild("SubmitBookBtn")
local menuTitle = createMenu:WaitForChild("MenuTitle")
local titleInput = createMenu:WaitForChild("TitleInput")
local priceInput = createMenu:WaitForChild("PriceInput")
local imageIdInput = createMenu:WaitForChild("ImageIdInput")
local imagePreview = createMenu:WaitForChild("ImagePreview")
local descInput = createMenu:WaitForChild("DescriptionInput")

local viewMenu = mainAppFrame:WaitForChild("ViewBookMenu")
local viewCloseBtn = viewMenu:WaitForChild("CloseMenuBtn")

local terminalPrompt = Workspace:WaitForChild("TerminalScreen"):WaitForChild("Keyboard"):WaitForChild("ProximityPrompt")

-- === STATE VARIABLES ===
local isDeleteMode = false
local isUpdateMode = false
local currentMenuMode = "Create"
local bookToUpdate = nil
local originalTitle = ""
local updateQueue = {}

-- === CORE SETUP FUNCTIONS ===
local function setupBookInteractive(newBook)
	local checkbox = newBook:WaitForChild("BookCheckbox")
	checkbox.Visible = false
	checkbox.MouseButton1Click:Connect(function()
		if checkbox.Text == "" then
			checkbox.Text = "✓"
			checkbox.TextColor3 = Color3.fromRGB(0, 200, 0)
		else
			checkbox.Text = ""
		end
	end)

	local viewBtn = newBook:WaitForChild("ViewButton")
	if viewBtn then
		viewBtn.MouseButton1Click:Connect(function()
			if isDeleteMode or isUpdateMode then return end
			UIHelper.SetupViewMenu(newBook, viewMenu)
		end)
	end
end

local function loadInventory()
	for _, child in pairs(bookGrid:GetChildren()) do
		if child:IsA("Frame") and child.Name ~= "BookTemplate" then
			child:Destroy()
		end
	end

	local realBooks = getBooks:InvokeServer()

	for _, bookData in pairs(realBooks) do
		local newBook = template:Clone()
		newBook.Name = bookData.title
		newBook.Visible = true

		newBook:WaitForChild("BookTitle").Text = bookData.title
		newBook:WaitForChild("BookPrice").Text = tostring(bookData.price)
		newBook:WaitForChild("BookDescription").Text = bookData.description or ""
		if bookData.imageId and bookData.imageId ~= "" then
			newBook:WaitForChild("BookCover").Image = bookData.imageId
		end

		setupBookInteractive(newBook)
		newBook.Parent = bookGrid
	end
end

-- === EVENTS & BUTTON CLICKS ===

terminalPrompt.Triggered:Connect(function(playerWhoTriggered)
	if playerWhoTriggered == player then
		loadInventory()
		mainAppFrame.Visible = true
		mouseUnlocker.Parent = mainAppFrame -- Unlocks the mouse!
		UserInputService.MouseIconEnabled = true -- Forces the arrow to appear!
	end
end)

closeButton.MouseButton1Click:Connect(function() 
	mainAppFrame.Visible = false 
	mouseUnlocker.Parent = nil -- Locks the mouse back to the center!
	UserInputService.MouseIconEnabled = false -- Hides the arrow!
end)

closeMenuBtn.MouseButton1Click:Connect(function() createMenu.Visible = false end)
viewCloseBtn.MouseButton1Click:Connect(function() viewMenu.Visible = false end)

deleteBtn.MouseButton1Click:Connect(function()
	if not isDeleteMode then
		isDeleteMode = true
		deleteBtn.Text = "Delete Selected"
		deleteBtn.TextColor3 = Color3.fromRGB(255, 50, 50)
		isUpdateMode = false
		updateBtn.Text = "Update Book"
		updateBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
		UIHelper.ToggleCheckboxes(bookGrid, true)
	else
		isDeleteMode = false
		deleteBtn.Text = "Delete Book"
		deleteBtn.TextColor3 = Color3.fromRGB(255, 255, 255)

		local toDelete = UIHelper.GetQueuedBooks(bookGrid)
		for _, item in pairs(toDelete) do
			bookEvent:FireServer("Delete", item.Name, "", "", "")
			item:Destroy()
		end
		UIHelper.ToggleCheckboxes(bookGrid, false)
	end
end)

createBtn.MouseButton1Click:Connect(function()
	currentMenuMode = "Create"
	menuTitle.Text = "Create a New Book"
	submitBtn.Text = "Add to Inventory"
	UIHelper.ClearInputMenu(titleInput, priceInput, descInput, imageIdInput, imagePreview)
	createMenu.Visible = true
end)

updateBtn.MouseButton1Click:Connect(function()
	if not isUpdateMode then
		isUpdateMode = true
		updateBtn.Text = "Update Selected"
		updateBtn.TextColor3 = Color3.fromRGB(50, 150, 255)
		isDeleteMode = false
		deleteBtn.Text = "Delete Book"
		deleteBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
		UIHelper.ToggleCheckboxes(bookGrid, true)
	else
		updateQueue = UIHelper.GetQueuedBooks(bookGrid)

		if #updateQueue > 0 then
			currentMenuMode = "Update"
			bookToUpdate = table.remove(updateQueue, 1)
			originalTitle = bookToUpdate.Name

			menuTitle.Text = "Update Book"
			submitBtn.Text = "Update Book"
			titleInput.Text = bookToUpdate:WaitForChild("BookTitle").Text
			priceInput.Text = bookToUpdate:WaitForChild("BookPrice").Text
			descInput.Text = bookToUpdate:WaitForChild("BookDescription").Text

			-- NEW: Grab the image, chop off "rbxassetid://", and paste the numbers!
			local currentImage = bookToUpdate:WaitForChild("BookCover").Image
			imageIdInput.Text = string.gsub(currentImage, "rbxassetid://", "")
			imagePreview.Image = currentImage

			createMenu.Visible = true
		end

		isUpdateMode = false
		updateBtn.Text = "Update Book"
		updateBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
		UIHelper.ToggleCheckboxes(bookGrid, false)
	end
end)

-- === SUBMIT BUTTON (WITH STRICT VALIDATION!) ===
submitBtn.MouseButton1Click:Connect(function()
	local newTitle = titleInput.Text
	local rawPrice = priceInput.Text
	local newImageId = imageIdInput.Text
	local newDesc = descInput.Text

	-- 1. BLANK CHECK
	if newTitle == "" or rawPrice == "" or newImageId == "" or newDesc == "" then 
		UIHelper.ShowError(submitBtn, "Please fill out all fields!")
		return 
	end

	-- 2. PRICE NUMBER CHECK
	local cleanPrice = string.gsub(rawPrice, "₱", "") 
	if tonumber(cleanPrice) == nil then
		UIHelper.ShowError(submitBtn, "Price must be numbers!")
		return
	end

	-- 3. IMAGE ID NUMBER CHECK
	if tonumber(newImageId) == nil then
		UIHelper.ShowError(submitBtn, "Image ID must be numbers!")
		return
	end

	local formattedPrice = UIHelper.FormatPeso(rawPrice)

	if currentMenuMode == "Create" then
		bookEvent:FireServer("Create", newTitle, formattedPrice, newImageId, newDesc, nil)

		local newBook = template:Clone()
		newBook.Name = newTitle
		newBook.Visible = true
		newBook:WaitForChild("BookTitle").Text = newTitle
		newBook:WaitForChild("BookPrice").Text = formattedPrice
		newBook:WaitForChild("BookDescription").Text = newDesc
		if newImageId ~= "" then newBook:WaitForChild("BookCover").Image = "rbxassetid://" .. newImageId end

		setupBookInteractive(newBook)
		newBook.Parent = bookGrid
		createMenu.Visible = false

	elseif currentMenuMode == "Update" then
		bookEvent:FireServer("Update", newTitle, formattedPrice, newImageId, newDesc, originalTitle)

		bookToUpdate.Name = newTitle
		bookToUpdate:WaitForChild("BookTitle").Text = newTitle
		bookToUpdate:WaitForChild("BookPrice").Text = formattedPrice
		bookToUpdate:WaitForChild("BookDescription").Text = newDesc
		if newImageId ~= "" then bookToUpdate:WaitForChild("BookCover").Image = "rbxassetid://" .. newImageId end
		bookToUpdate:WaitForChild("BookCheckbox").Text = ""

		if #updateQueue > 0 then
			bookToUpdate = table.remove(updateQueue, 1)
			originalTitle = bookToUpdate.Name
			titleInput.Text = bookToUpdate:WaitForChild("BookTitle").Text
			priceInput.Text = bookToUpdate:WaitForChild("BookPrice").Text
			descInput.Text = bookToUpdate:WaitForChild("BookDescription").Text

			-- NEW: Do the same image ID recovery for the next queued book!
			local nextImage = bookToUpdate:WaitForChild("BookCover").Image
			imageIdInput.Text = string.gsub(nextImage, "rbxassetid://", "")
			imagePreview.Image = nextImage
		else
			createMenu.Visible = false
		end
	end
end)