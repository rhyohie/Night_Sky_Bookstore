local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer
local camera = Workspace.CurrentCamera

local triggerZone = Workspace:WaitForChild("CutsceneTrigger")
local giantCam = Workspace:WaitForChild("GiantCam")
local giantModel = Workspace:WaitForChild("GhostModel") 

local hasPlayed = false 

-- === CREATE THE SUBTITLE UI ===
local playerGui = player:WaitForChild("PlayerGui")
local cinematicGui = Instance.new("ScreenGui")
cinematicGui.Name = "CinematicGui"
cinematicGui.Parent = playerGui

local subtitleBackground = Instance.new("Frame")
subtitleBackground.Size = UDim2.new(1, 0, 0.15, 0)
subtitleBackground.Position = UDim2.new(0, 0, 1, 0) 
subtitleBackground.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
subtitleBackground.BackgroundTransparency = 0.3
subtitleBackground.BorderSizePixel = 0
subtitleBackground.Parent = cinematicGui

local subtitleText = Instance.new("TextLabel")
subtitleText.Size = UDim2.new(0.8, 0, 0.8, 0)
subtitleText.Position = UDim2.new(0.1, 0, 0.1, 0)
subtitleText.BackgroundTransparency = 1
subtitleText.TextColor3 = Color3.fromRGB(255, 255, 255)
subtitleText.TextScaled = true
subtitleText.Font = Enum.Font.GothamMedium
subtitleText.Text = ""
subtitleText.Parent = subtitleBackground


-- === THE TYPEWRITER EFFECT ===
local function speak(text)
	subtitleText.Text = ""
	for i = 1, #text do
		subtitleText.Text = string.sub(text, 1, i)
		task.wait(0.04) 
	end
	task.wait(2.5) 
end


-- === PARTICLE GENERATOR (NEW!) ===
local function createLightParticles(part)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = ColorSequence.new(Color3.fromRGB(255, 255, 200)) -- Warm, glowing golden light
	emitter.LightEmission = 1 -- Makes the particles actually glow in the dark
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.6),
		NumberSequenceKeypoint.new(1, 0) -- The particles will slowly shrink into nothing
	})
	emitter.Lifetime = NumberRange.new(1.5, 3)
	emitter.Speed = NumberRange.new(2, 6)
	emitter.SpreadAngle = Vector2.new(180, 180) -- Shoot in all directions
	emitter.Acceleration = Vector3.new(0, 3, 0) -- Float upwards smoothly
	emitter.Drag = 2 -- Slows them down naturally as they drift
	emitter.Rate = 0 -- Keeps them turned off until we manually fire them!
	emitter.Parent = part

	return emitter
end


-- === THE MAIN CUTSCENE ===
local function playCinematic()
	-- 1. Freeze the player
	local character = player.Character
	if character and character:FindFirstChild("Humanoid") then
		character.Humanoid.WalkSpeed = 0
	end

	-- 2. Take the camera and glide it up to the giant
	camera.CameraType = Enum.CameraType.Scriptable
	local cameraMove = TweenService:Create(
		camera, 
		TweenInfo.new(3, Enum.EasingStyle.Cubic, Enum.EasingDirection.InOut), 
		{CFrame = giantCam.CFrame}
	)
	cameraMove:Play()
	cameraMove.Completed:Wait() 

	-- 3. Slide the subtitle bar up and make the giant talk
	TweenService:Create(subtitleBackground, TweenInfo.new(0.5), {Position = UDim2.new(0, 0, 0.85, 0)}):Play()
	task.wait(0.5)

	speak("Welcome, traveler, to the Astral Archives... a sanctuary of forgotten whispers.")
	speak("For millennia, I have anchored these ancient tomes against the tides of time.")
	speak("Yet, my essence fades, and the constellations call me back to the void.")
	speak("I entrust this grand repository to your hands.")
	speak("Manage its wisdom well, new Keeper... the night sky is yours to chronicle.")

	TweenService:Create(subtitleBackground, TweenInfo.new(0.5), {Position = UDim2.new(0, 0, 1, 0)}):Play()

	-- 4. THE LIGHT DISPERSION VANISH (NEW!)

	-- Phase A: Make the giant glow white-hot
	local glowTween = TweenInfo.new(1.5, Enum.EasingStyle.Sine)
	for _, part in pairs(giantModel:GetDescendants()) do
		if part:IsA("BasePart") then
			part.Material = Enum.Material.Neon -- Instantly turns on the glow effect
			TweenService:Create(part, glowTween, {Color = Color3.fromRGB(255, 255, 255)}):Play()
		end
	end

	task.wait(1.5) -- Wait for the glow to reach its peak

	-- Phase B: The Shatter and Disperse
	local instantVanish = TweenInfo.new(0.2, Enum.EasingStyle.Linear)
	for _, part in pairs(giantModel:GetDescendants()) do
		if part:IsA("BasePart") then
			-- Create and trigger the particle burst
			local spark = createLightParticles(part)
			spark:Emit(15) -- Shoots 15 glowing orbs from every single body part!

			-- Instantly turn the physical body invisible
			TweenService:Create(part, instantVanish, {Transparency = 1}):Play()
		elseif part:IsA("Decal") then
			TweenService:Create(part, instantVanish, {Transparency = 1}):Play()
		end
	end

	task.wait(3.5) -- Wait for the floating embers to drift away and burn out

	-- 5. Clean up and give control back
	giantModel:Destroy() 
	camera.CameraType = Enum.CameraType.Custom
	if character and character:FindFirstChild("Humanoid") then
		character.Humanoid.WalkSpeed = 16 
	end
end


-- === THE TRIGGER LISTENER ===
triggerZone.Touched:Connect(function(hit)
	if not hasPlayed then
		local character = player.Character
		if character and hit:IsDescendantOf(character) then
			hasPlayed = true 
			playCinematic()
		end
	end
end)