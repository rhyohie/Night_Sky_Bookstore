local UIHelper = {}

-- 1. Formats the price safely with a Peso sign
function UIHelper.FormatPeso(rawPrice)
	local clean = string.gsub(tostring(rawPrice), "₱", "")
	return "₱" .. clean
end

-- 2. Shows or hides the checkboxes across the grid
function UIHelper.ToggleCheckboxes(bookGrid, show)
	for _, item in pairs(bookGrid:GetChildren()) do
		if item:IsA("Frame") and item.Name ~= "BookTemplate" then
			local box = item:FindFirstChild("BookCheckbox")
			if box then
				box.Visible = show
				if not show then box.Text = "" end
			end
		end
	end
end

-- 3. Returns a neat list of every book the user checked
function UIHelper.GetQueuedBooks(bookGrid)
	local queue = {}
	for _, item in pairs(bookGrid:GetChildren()) do
		if item:IsA("Frame") and item.Name ~= "BookTemplate" then
			local box = item:FindFirstChild("BookCheckbox")
			if box and box.Text == "✓" then
				table.insert(queue, item)
			end
		end
	end
	return queue
end

-- 4. Instantly clears out the Create Menu text boxes
function UIHelper.ClearInputMenu(titleInput, priceInput, descInput, imageIdInput, imagePreview)
	titleInput.Text = ""
	priceInput.Text = ""
	descInput.Text = ""
	imageIdInput.Text = ""
	imagePreview.Image = ""
end

-- 5. Sets up the View Menu with the selected book's data
function UIHelper.SetupViewMenu(bookFrame, viewMenu)
	local viewTitle = viewMenu:WaitForChild("TitleInput")
	local viewPrice = viewMenu:WaitForChild("PriceInput")
	local viewImage = viewMenu:WaitForChild("ImagePreview")
	local viewDesc = viewMenu:WaitForChild("DescriptionInput")

	viewTitle.Text = bookFrame:WaitForChild("BookTitle").Text
	viewPrice.Text = bookFrame:WaitForChild("BookPrice").Text
	viewImage.Image = bookFrame:WaitForChild("BookCover").Image
	viewDesc.Text = bookFrame:WaitForChild("BookDescription").Text

	viewMenu.Visible = true
end

-- 6. VISUAL ERROR WARNING (NEW!)
function UIHelper.ShowError(button, message)
	-- Save the original look of the button
	local originalText = button.Text
	local originalColor = button.TextColor3

	-- Change it to a red warning!
	button.Text = message
	button.TextColor3 = Color3.fromRGB(255, 50, 50) 

	-- Wait 2 seconds, then change it back to normal
	task.wait(2)
	button.Text = originalText
	button.TextColor3 = originalColor
end

return UIHelper