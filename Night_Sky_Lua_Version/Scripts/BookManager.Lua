local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local bookEvent = ReplicatedStorage:WaitForChild("BookEvent")
local GetBooks = ReplicatedStorage:WaitForChild("GetBooks")

-- Connects to the official Roblox cloud database!
local BookStoreDB = DataStoreService:GetDataStore("BookStoreInventory_V1")

-- A dictionary that will hold each player's unique inventory while they play
local playerInventories = {}

-- === 1. LOAD DATA WHEN A PLAYER JOINS ===
Players.PlayerAdded:Connect(function(player)
	-- Ask the cloud database if this player has saved data
	local success, savedData = pcall(function()
		return BookStoreDB:GetAsync(player.UserId)
	end)

	if success and savedData then
		-- Load their saved books!
		playerInventories[player.UserId] = savedData
		print("[SERVER]: Loaded saved inventory for " .. player.Name)
	else
		-- If they are a new player, give them a starter book
		playerInventories[player.UserId] = {
			{
				id = 1,
				title = "The Great Gatsby",
				price = "₱15.99",
				imageId = "rbxassetid://95536000860334",
				description = "A classic novel about the American Dream in the 1920s." 
			}
		}
		print("[SERVER]: Created new starter inventory for " .. player.Name)
	end
end)

-- === 2. SAVE DATA WHEN A PLAYER LEAVES ===
Players.PlayerRemoving:Connect(function(player)
	local inventoryToSave = playerInventories[player.UserId]

	if inventoryToSave then
		local success, errorMessage = pcall(function()
			BookStoreDB:SetAsync(player.UserId, inventoryToSave)
		end)

		if success then
			print("[SERVER]: Successfully saved inventory for " .. player.Name)
		else
			warn("[SERVER]: Failed to save for " .. player.Name .. " - " .. tostring(errorMessage))
		end

		-- Clear them from active memory to prevent lag
		playerInventories[player.UserId] = nil
	end
end)

-- === 3. EMERGENCY SAVE FOR ROBLOX STUDIO ===
-- When you hit 'Stop' in Studio, the server closes so fast that 'PlayerRemoving' sometimes doesn't fire. This forces it to save!
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		local inventoryToSave = playerInventories[player.UserId]
		if inventoryToSave then
			BookStoreDB:SetAsync(player.UserId, inventoryToSave)
		end
	end
end)


-- === 4. NETWORK LISTENERS (UPDATED FOR PER-PLAYER DATA) ===
bookEvent.OnServerEvent:Connect(function(player, action, newTitle, newPrice, newImageId, newDescription, oldTitle)
	-- Grab the specific inventory belonging to the player who clicked the button
	local inventory = playerInventories[player.UserId]
	if not inventory then return end

	if action == "Create" then
		local newBook = {
			id = #inventory + 1,
			title = newTitle,
			price = newPrice,
			imageId = "rbxassetid://" .. newImageId,
			description = newDescription 
		}
		table.insert(inventory, newBook)
		print("[SERVER]: " .. player.Name .. " created '" .. newTitle .. "'!")

	elseif action == "Delete" then
		for i = #inventory, 1, -1 do
			if inventory[i].title == newTitle then 
				table.remove(inventory, i)
				print("[SERVER]: " .. player.Name .. " deleted '" .. newTitle .. "'!")
			end
		end

	elseif action == "Update" then
		for _, book in pairs(inventory) do
			if book.title == oldTitle then
				book.title = newTitle
				book.price = newPrice
				book.description = newDescription 

				if newImageId and newImageId ~= "" then
					book.imageId = "rbxassetid://" .. newImageId
				end

				print("[SERVER]: " .. player.Name .. " updated '" .. oldTitle .. "' to '" .. newTitle .. "'!")
				break 
			end
		end
	end	
end)

-- === 5. HAND OVER THE BOOKS TO THE UI ===
GetBooks.OnServerInvoke = function(player)
	-- Give the UI the player's specific inventory (or an empty table if it hasn't loaded yet)
	return playerInventories[player.UserId] or {}
end