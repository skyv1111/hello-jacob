import pygame
import sys
from scripts.building_data import building_data as buildingData
from scripts.category_data import category_data as categoryData

pygame.init()
pygame.mixer.init()
info = pygame.display.Info()
clock = pygame.time.Clock()

cellWidth, cellHeight = 40, 30
gridWidth, gridHeight = 60, 50
gridSize = (cellWidth, cellHeight)

WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("City Simulator")

font = pygame.font.Font(None, 36)
buildingsList = []
backgroundImage = pygame.transform.scale(pygame.image.load("images/misc/background.png").convert(), (gridWidth * cellWidth, gridHeight * cellHeight))
grid = [[0 for _ in range(gridWidth)] for _ in range(gridHeight)]

cameraX, cameraY = 175, 340
maxCameraX = (gridWidth - WIDTH // cellWidth) * cellWidth
maxCameraY = (gridHeight - HEIGHT // cellHeight) * cellHeight

showGrid = True

def screenToGrid(screenX, screenY):
    return (screenX + cameraX) // cellWidth, (screenY + cameraY) // cellHeight

def renderGridlines():
    gridSurface = pygame.Surface((gridWidth * cellWidth, gridHeight * cellHeight), pygame.SRCALPHA)
    gridSurface.set_alpha(50)

    for x in range(0, gridWidth * cellWidth, gridSize[0]):
        pygame.draw.line(gridSurface, (0, 0, 0), (x - cameraX, 0), (x - cameraX, HEIGHT), 2)

    for y in range(0, gridHeight * cellHeight, gridSize[1]):
        pygame.draw.line(gridSurface, (0, 0, 0), (0, y - cameraY), (WIDTH, y - cameraY), 2)

    screen.blit(gridSurface, (0, 0))

selectedBuildingPreview = {"type": "road_3way", "rotation": "north", "x": 0, "y": 0}

def rotateBuilding(selectedBuildingPreview):
    buildingType, currentRotation, rotations = selectedBuildingPreview["type"], selectedBuildingPreview["rotation"], ["north", "east", "south", "west"]
    nextRotationIndex = (rotations.index(currentRotation) + 1) % len(rotations)
    selectedBuildingPreview["rotation"] = rotations[nextRotationIndex]

def isValidPosition(buildingType, gridX, gridY, buildingRotation, buildingsList):
    buildingWidth = buildingData[buildingType]["Rotations"][buildingRotation]["Width"]
    buildingHeight = buildingData[buildingType]["Rotations"][buildingRotation]["Height"]
    
    if 0 <= gridX < gridWidth and 0 <= gridY < gridHeight:
        for building in buildingsList:
            bType, bRotation = building["type"], building["rotation"]
            bWidth, bHeight = (
                buildingData[bType]["Rotations"][bRotation]["Width"],
                buildingData[bType]["Rotations"][bRotation]["Height"],
            )
            if (
                building["x"] < gridX + buildingWidth
                and building["x"] + bWidth > gridX
                and building["y"] < gridY + buildingHeight
                and building["y"] + bHeight > gridY
            ):
                return False
        return True
    return False

def renderBuilding(building, cameraX, cameraY):
    buildingType, buildingRotation, buildingX, buildingY = building["type"], building["rotation"], building["x"], building["y"]
    renderX, renderY = buildingX * cellWidth - cameraX - cellWidth, buildingY * cellHeight - cameraY - cellHeight
    imagePath = buildingData[buildingType]["Rotations"][buildingRotation]['ImagePath']
    buildingImage = pygame.image.load(imagePath).convert_alpha()
    screen.blit(buildingImage, (renderX, renderY))

def renderBuildingPreview(buildingType, buildingRotation, mouseX, mouseY):
    gridX, gridY = screenToGrid(mouseX, mouseY)
    tintColor = (50, 200, 50) if isValidPosition(buildingType, gridX, gridY, buildingRotation, buildingsList) else (200, 50, 50)
    renderX, renderY = gridX * cellWidth - cameraX - cellWidth, gridY * cellHeight - cameraY - cellHeight
    imagePath = buildingData[buildingType]["Rotations"][buildingRotation]['ImagePath']
    buildingImage = pygame.image.load(imagePath).convert_alpha()
    tintedBuildingImage = tintBuildingImage(buildingImage, tintColor)
    screen.blit(tintedBuildingImage, (renderX, renderY))

def tintBuildingImage(buildingImage, tintColor):
    tintedImage = buildingImage.copy()
    tintedImage.fill(tintColor, special_flags=pygame.BLEND_RGBA_MULT)
    tintedImage.set_alpha(128)
    return tintedImage

def isSpaceFree(x, y, WIDTH, HEIGHT, grid):
    for i in range(WIDTH):
        for j in range(HEIGHT):
            if grid[y + j][x + i] == 1:
                return False
    return True

def isMouseOverUI(mouse_x, mouse_y):
    return mouse_y > HEIGHT - ui_height - 100 if active_category else mouse_y > HEIGHT - ui_height

def isMouseInBuilding(building, mouseX, mouseY):
    buildingType, buildingRotation = building["type"], building["rotation"]
    buildingDataRotated = buildingData[buildingType]["Rotations"][buildingRotation]
    buildingX, buildingY = building["x"], building["y"]
    buildingWidth, buildingHeight = buildingDataRotated["Width"], buildingDataRotated["Height"]
    buildingRect = pygame.Rect(
        buildingX * cellWidth - cameraX, buildingY * cellHeight - cameraY,
        buildingWidth * cellWidth, buildingHeight * cellHeight
    )
    return buildingRect.collidepoint(mouseX, mouseY)

ui_height = 100
button_background_image = pygame.image.load("images/ui/category_background.png").convert_alpha()
highlight_image = pygame.image.load("images/ui/highlight.png").convert_alpha()

button_padding, button_size = 10, (75, 75)

active_category = None
prev_mouse_state = 0

def draw_ui_button(category, data, rect):
    button_image = pygame.image.load(data["ImagePath"]).convert_alpha()
    if active_category == category:
        button_image = tintBuildingImage(button_image, (255, 255, 255))
        screen.blit(highlight_image, (rect.x, rect.y + rect.height + 3))
    screen.blit(pygame.transform.scale(button_image, button_size), rect.topleft)

def draw_ui():
    global active_category, prev_mouse_state

    ui_surface = pygame.Surface((WIDTH, ui_height), pygame.SRCALPHA)
    ui_surface.blit(pygame.transform.scale(button_background_image, (WIDTH, ui_height)), (0, 0))
    screen.blit(ui_surface, (0, HEIGHT - ui_height))

    total_buttons_width = len(categoryData) * (button_size[0] + button_padding) - button_padding
    starting_x = (WIDTH - total_buttons_width) // 2
    starting_y = HEIGHT - ui_height + button_padding + (ui_height - 2 * button_padding - button_size[1]) // 2

    mouse_state = pygame.mouse.get_pressed()[0]

    for category, data in categoryData.items():
        button_rect = pygame.Rect(starting_x, starting_y, *button_size)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_x, mouse_y) and mouse_state and not prev_mouse_state:
            active_category = None if active_category == category else category
        draw_ui_button(category, data, button_rect)
        starting_x += button_size[0] + button_padding

    prev_mouse_state = mouse_state
    draw_category_frames()

def draw_category_frames():
    prev_mouse_state = False
    if active_category is not None:
        frame_rect = pygame.Rect(0, HEIGHT - ui_height - 100, WIDTH, 100)
        frame_background = pygame.transform.scale(pygame.image.load("images/ui/building_background.png").convert_alpha(), frame_rect.size)
        screen.blit(frame_background, frame_rect.topleft)
        category_buildings = [building for building in buildingData.values() if building['Category'] == active_category]
        building_width = (WIDTH - 2 * button_padding - (len(category_buildings) - 1) * button_padding) // len(category_buildings)
        for idx, building in enumerate(category_buildings):
            x_position = button_padding + idx * (building_width + button_padding)
            button_background_rect = pygame.Rect(x_position, HEIGHT - ui_height - 80, building_width, 80)
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if button_background_rect.collidepoint(mouse_x, mouse_y):
                if pygame.mouse.get_pressed()[0] and not prev_mouse_state:
                    selectedBuildingPreview["type"] = building["Type"]
            screen.blit(pygame.transform.scale(pygame.image.load("images/ui/button_background.png").convert_alpha(), (button_background_rect.width, button_background_rect.height)), button_background_rect.topleft)
            name_font, desc_font, info_font = pygame.font.Font(None, 24), pygame.font.Font(None, 15), pygame.font.Font(None, 15)
            name_render, desc_render = name_font.render(building['Name'], True, (255, 255, 255)), desc_font.render(building['Description'], True, (255, 255, 255))
            name_text_rect, desc_text_rect = name_render.get_rect(midtop=(x_position + building_width / 2, HEIGHT - ui_height - 75)), desc_render.get_rect(midtop=(x_position + building_width / 2, HEIGHT - ui_height - 55))
            building_image_path = building['Rotations']['north']['ImagePath']
            building_image = pygame.image.load(building_image_path).convert_alpha()

            building_image_height = 5 * (button_background_rect.height - 20)
            building_image_width = int(building_image_height * building_image.get_width() / building_image.get_height())
            building_image = pygame.transform.scale(building_image, (building_image_width, building_image_height))
            building_image_rect = building_image.get_rect(center=button_background_rect.center)
            clip_rect = screen.get_clip()
            screen.set_clip(button_background_rect)
            building_image.set_alpha(50)
            screen.blit(building_image, building_image_rect.topleft)
            screen.set_clip(clip_rect)
            screen.blit(name_render, name_text_rect)
            screen.blit(desc_render, desc_text_rect)
            necessary_info = building.get('Information', [])
            info_text_lines = [
                f"{info}: ${building[info]}p/m" if info in ['Maintenance', 'Revenue'] else f"{info}: ${building[info]}" if info == 'Cost' else f"{info}: +{building[info]}" for info in necessary_info
            ]
            info_text = '\n'.join(info_text_lines)
            info_render = info_font.render(info_text, True, (255, 255, 255))
            info_text_rect = info_render.get_rect(midtop=(x_position + building_width / 2, HEIGHT - ui_height - 40))
            screen.blit(info_render, info_text_rect)
        
        prev_mouse_state = pygame.mouse.get_pressed()[0]

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                showGrid = not showGrid
            elif event.key == pygame.K_r:
                rotateBuilding(selectedBuildingPreview)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if not isMouseOverUI(mouse_x, mouse_y):
                if event.button == 1:
                    grid_x, grid_y = screenToGrid(mouse_x, mouse_y)
                    building_type = selectedBuildingPreview["type"]
                    building_rotation = selectedBuildingPreview["rotation"]
                    building_width = buildingData[building_type]["Rotations"][building_rotation]['Width']
                    building_height = buildingData[building_type]["Rotations"][building_rotation]['Height']

                    if isSpaceFree(grid_x, grid_y, building_width, building_height, grid):
                        action = 1  # 1 for placement
                        for i in range(building_width):
                            for j in range(building_height):
                                grid[grid_y + j][grid_x + i] = action
                        buildingsList.append({"type": building_type, "rotation": building_rotation, "x": grid_x, "y": grid_y})
                elif event.button == 3:
                    action = 0  # 0 for deletion
                    for building in buildingsList:
                        if isMouseInBuilding(building, mouse_x, mouse_y):
                            building_width = buildingData[building["type"]]["Rotations"][building["rotation"]]['Width']
                            building_height = buildingData[building["type"]]["Rotations"][building["rotation"]]['Height']
                            for i in range(building_width):
                                for j in range(building_height):
                                    grid[building["y"] + j][building["x"] + i] = action
                            buildingsList.remove(building)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        cameraY = max(0, cameraY - 5)
    if keys[pygame.K_s]:
        cameraY = min(maxCameraY, cameraY + 5)
    if keys[pygame.K_a]:
        cameraX = max(0, cameraX - 5)
    if keys[pygame.K_d]:
        cameraX = min(maxCameraX, cameraX + 5)

    screen.blit(backgroundImage, (-cameraX, -cameraY))

    for building in sorted(buildingsList, key=lambda b: (b["y"], b["x"]), reverse=False):
        renderBuilding(building, cameraX, cameraY)

    if showGrid:
        renderGridlines()

    if selectedBuildingPreview:
        selectedBuildingType = selectedBuildingPreview["type"]
        selectedBuildingRotation = selectedBuildingPreview["rotation"]
        renderBuildingPreview(selectedBuildingType, selectedBuildingRotation, *pygame.mouse.get_pos())
        
    draw_ui()

    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (0, 0, 0))
    screen.blit(fps_text, (10, 10))

    clock.tick(60)
    
    pygame.display.flip()
