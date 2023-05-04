import numpy as np
import random
import matplotlib.pyplot as plt
from PIL import Image


def draw_bounds(image, x1, y1, x2, y2, color):
  # Draw horizontal lines
  image[y1, x1:x2 + 1] = color
  image[y2, x1:x2 + 1] = color
  # Draw vertical lines
  image[y1:y2 + 1, x1] = color
  image[y1:y2 + 1, x2] = color


def fill_bounds(image, x1, y1, x2, y2, color):
  for i in range(x1, x2 + 1):
    for j in range(y1, y2 + 1):
      image[i, j] = color
	  
	  
def building_size(horizontal_bounds, horizontal_max, vertical_bounds, vertical_max):
  horizontal_lower_third = horizontal_max / 3
  horizontal_upper_third = horizontal_max * 2 / 3
  vertical_lower_third = vertical_max / 3
  vertical_upper_third = vertical_max * 2 / 3
  
  if horizontal_bounds < horizontal_lower_third and vertical_bounds < vertical_lower_third:
    return "small "
  elif horizontal_bounds < horizontal_upper_third and vertical_bounds < vertical_upper_third:
    return ""
  else:
    return "large "
	
def image_contains_color(image_array, tolerance=0):
    diff = np.abs(image_array[..., :-1] - image_array[..., 1:])
    max_diff = np.max(diff, axis=-1)
    return np.any(max_diff > tolerance)


def scale_image_nn(image_array, scale_factor):
  # Get the dimensions of the original image
  height, width, channels = image_array.shape

  # Calculate the new dimensions for the scaled image
  new_height, new_width = int(height * scale_factor), int(width * scale_factor)

  # Create an empty array for the scaled image
  scaled_array = np.zeros((new_height, new_width, channels),
                          dtype=image_array.dtype)

  # Calculate the scaling factor for each dimension
  y_scale = height / new_height
  x_scale = width / new_width

  # Perform nearest-neighbor interpolation
  for y in range(new_height):
    for x in range(new_width):
      # Calculate the corresponding pixel in the original image
      original_y = int(y * y_scale)
      original_x = int(x * x_scale)

      # Copy the color of the nearest neighbor in the original image
      scaled_array[y, x] = image_array[original_y, original_x]

  # Return the scaled image
  return scaled_array


def replace_rectangles(image_array, color, replacement_image, x_size, y_size,
                       flip_chance, up_down, scale_factor):
  windows_img = Image.open(replacement_image)
  if image_array.shape[2] == 3:
    windows_img = windows_img.convert('RGB')
  else:
    windows_img = windows_img.convert('RGBA')

  # Create a mask of pixels that match the specified color
  mask = np.all(image_array == color, axis=-1)

  # Find the coordinates of the top-left corner of each rectangle
  rectangles = []
  for y in range(mask.shape[0]):
    for x in range(mask.shape[1]):
      if mask[y, x]:
        # Check if this is the top-left corner of a new rectangle
        if (y == 0 or not mask[y - 1, x]) and (x == 0 or not mask[y, x - 1]):
          rectangles.append((x, y))

  # Replace each rectangular area with the replacement image
  # Flip the replacement image with the given chance
  replacements = 0
  for x, y in rectangles:
    y_start, x_start = y, x
    
    if random.random() < flip_chance:
      if up_down:
        windows_img_t = windows_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        windows_array = np.array(windows_img_t)
        y_start = y - y_size + scale_factor
      else:
        windows_img_t = windows_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        windows_array = np.array(windows_img_t)
        x_start = x - x_size + scale_factor
    else:
      windows_array = np.array(windows_img)

    black_pixels_mask = np.all(windows_array == [0, 0, 0], axis=-1)
    black_pixels_mask_expanded = np.expand_dims(black_pixels_mask, axis=-1)

    inside_rectangle_mask = np.zeros_like(mask, dtype=bool)
    inside_rectangle_mask[y_start:y_start + y_size, x_start:x_start + x_size] = True

    combined_mask = black_pixels_mask_expanded & inside_rectangle_mask[y_start:y_start + y_size, x_start:x_start + x_size, np.newaxis]

    image_array[y_start:y_start + y_size, x_start:x_start + x_size][np.repeat(combined_mask, image_array.shape[2], axis=-1)] = windows_array[np.repeat(combined_mask, image_array.shape[2], axis=-1)]

    # Replace the detected rectangles with the replacement_image
    mask_expanded = np.expand_dims(mask, axis=-1)
    image_array[y_start:y_start + y_size, x_start:x_start + x_size][np.repeat(mask_expanded[y_start:y_start + y_size, x_start:x_start + x_size], image_array.shape[2], axis=-1)] = windows_array[np.repeat(mask_expanded[y_start:y_start + y_size, x_start:x_start + x_size], image_array.shape[2], axis=-1)]

    replacements += 1

  return replacements

def replace_color(np_image, old_color, new_color):
    # Create a boolean mask that is True where the old_color is found in the image
    color_mask = np.all(np_image == old_color, axis=-1)

    # Replace old_color with new_color using the mask
    np_image[color_mask] = new_color

    return np_image


###############################
### 0. Procedural generation configuration ###
number_of_generations = 6
##Canvas
min_height = 60
max_height = 120
min_width = 60
max_width = 120
bg_color = [255, 255, 255]
##Structure
margin = 10
min_rooms = 4
max_rooms = 9
##Additional elements
door_size = 4
window_size = 4
outer_door_probability = 20
inner_door_probability = 50
window_probability = 75
##Final colors
horizontal_inner_wall_color = [125, 125, 125]
horizontal_outer_wall_color = [0, 0, 0]
vertical_inner_wall_color = [125, 125, 125]
vertical_outer_wall_color = [0, 0, 0]
horizontal_door_color = [255, 0, 0]
vertical_door_color = [255, 255, 0]
horizontal_window_color = [0, 0, 255]
vertical_window_color = [0, 255, 255]
##Don't alter
scale_factor = 30

successfull_generations = 0
for img_nr in range(0, number_of_generations):
  #########################################################
  ### 1. Generate and draw basic bounds of the building ###

  #Establish bounds
  height = random.randrange(min_height, max_height)
  width = random.randrange(min_width, max_width)
  bounds_height = height - margin * 2
  bounds_width = width - margin * 2

  #Generate image background
  img = np.ones((width, height, 3), dtype=np.uint8)
  for i in range(0, height):
    for j in range(0, width):
      img[j, i] = bg_color

  #Draw building bounds
  wall_color = [0, 0, 255]
  floor_color = [255, 255, 0]
  draw_bounds(img, margin, margin, margin + bounds_height,
              margin + bounds_width, wall_color)
  fill_bounds(img, margin + 1, margin + 1, margin + bounds_width - 1,
              margin + bounds_height - 1, floor_color)

  ###############################################################
  ### 2. Generate room extents through growth-based algorithm ###

  #Class for keeping room extents
  class Room:

    def __init__(self, ptx, pty, color):
      self.x1 = ptx
      self.y1 = pty
      self.x2 = ptx
      self.y2 = pty
      self.color = color

  #Randomly generate starting points within the bounds
  room_nr = random.randrange(min_rooms, max_rooms)
  rooms = []
  for r in range(0, room_nr):
    room_color = [
      random.randrange(0, 255),
      random.randrange(0, 255),
      random.randrange(0, 255)
    ]
    pt_x = random.randrange(margin + 1, margin + bounds_width - 1)
    pt_y = random.randrange(margin + 1, margin + bounds_height - 1)
    img[pt_x, pt_y] = room_color
    rooms.append(Room(pt_x, pt_y, room_color))

  #Growth-based algorithm
  steps = height - margin  #The maximum amount of pixels a room can grow
  for s in range(0, steps):
    for r in rooms:
      #Grow upwards
      #Check upper edge
      up_clear = True
      for y in range(r.y1, r.y2 + 1):
        if (img[r.x1 - 1, y].tolist() not in [floor_color, wall_color]):
          up_clear = False
      if (up_clear):
        r.x1 -= 1
        for y in range(r.y1, r.y2 + 1):
          img[r.x1, y] = r.color
      #Grow downwards
      #Check lower edge
      down_clear = True
      for y in range(r.y1, r.y2 + 1):
        if (img[r.x2 + 1, y].tolist() not in [floor_color, wall_color]):
          down_clear = False
      if (down_clear):
        r.x2 += 1
        for y in range(r.y1, r.y2 + 1):
          img[r.x2, y] = r.color
      #Grow left
      #Check left edge
      left_clear = True
      for x in range(r.x1, r.x2 + 1):
        if (img[x, r.y1 - 1].tolist() not in [floor_color, wall_color]):
          left_clear = False
      if (left_clear):
        r.y1 -= 1
        for x in range(r.x1, r.x2 + 1):
          img[x, r.y1] = r.color
      #Grow right
      #Check right edge
      right_clear = True
      for x in range(r.x1, r.x2 + 1):
        if (img[x, r.y2 + 1].tolist() not in [floor_color, wall_color]):
          right_clear = False
      if (right_clear):
        r.y2 += 1
        for x in range(r.x1, r.x2 + 1):
          img[x, r.y2] = r.color

  #Remove all pixels that were not grown over from the building (by recoloring to background)
  for i, color in np.ndenumerate(img):
    if (color == floor_color).all():
      img[i] = bg_color

  #Eliminate rooms at random to create non-square building structures
  delete_list = []
  for r in rooms:
    if random.randint(0, 100) < 15:
      delete_list.append(r)
      #r.color = bg
      fill_bounds(img, r.x1, r.y1, r.x2, r.y2, bg_color)
  rooms = [r for r in rooms if r not in delete_list]

  ####################################################
  ### 3. Draw walls along the borders of the rooms ###

  #Draw inner and outer walls, make sure that they are one pixel thick
  outer_wall_color = [255, 0, 0]
  for r in rooms:
    #If a room was eliminated to be background, ignore
    if (r.color == bg_color):
      continue
    #Draw the edges - depening on which color the edge runs along, make it an outer or inner
    #Draw lower edge
    for i in range(r.y1, r.y2 + 1):
      if (img[r.x2 + 1, i].tolist() == bg_color):
        img[r.x2, i] = outer_wall_color
      else:
        img[r.x2, i] = wall_color
    #Draw upper edge
    for i in range(r.y1, r.y2 + 1):
      if (img[r.x1 - 1, i].tolist() == bg_color):
        img[r.x1 - 1, i] = outer_wall_color
      else:
        img[r.x1 - 1, i] = wall_color
    #Draw left edge
    for i in range(r.x1, r.x2 + 1):
      if (img[i, r.y1 - 1].tolist() == bg_color):
        img[i, r.y1] = outer_wall_color
      else:
        img[i, r.y1] = wall_color
    #Draw right edge
    for i in range(r.x1 - 1, r.x2 + 1):
      if (img[i, r.y2 + 1].tolist() == bg_color):
        img[i, r.y2 + 1] = outer_wall_color
      else:
        img[i, r.y2 + 1] = wall_color

  #############################################################################
  ### 4. Collect all necessary topological information from the drawn image ###

  #Mark and collect wall intersection points (nodes)
  nodes = set()
  node_color = [0, 255, 0]
  for r in rooms:
    img[r.x1 - 1, r.y1] = node_color
    nodes.add((r.x1 - 1, r.y1))
    img[r.x1 - 1, r.y2 + 1] = node_color
    nodes.add((r.x1 - 1, r.y2 + 1))
    img[r.x2, r.y2 + 1] = node_color
    nodes.add((r.x2, r.y2 + 1))
    img[r.x2, r.y1] = node_color
    nodes.add((r.x2, r.y1))
    fill_bounds(img, r.x1, r.y1 + 1, r.x2 - 1, r.y2, bg_color)

  #For every wall intersection point iterate right and downwards, to collect all walls in the image and distinguish them by type and direction
  horizontal_inner_edges = []
  horizontal_outer_edges = []
  vertical_inner_edges = []
  vertical_outer_edges = []
  for n in nodes:
    x, y = n
    wall_color = ""
    # Check for edge in lower direction
    for j in range(x + 1, width):
      if (img[j, y].tolist() == bg_color): break
      node_found = False
      for n2 in nodes:
        if (j, y) == n2:
          if (wall_color == outer_wall_color):
            vertical_outer_edges.append((n, n2[0] - n[0]))
          elif (wall_color == wall_color):
            vertical_inner_edges.append((n, n2[0] - n[0]))
          node_found = True
          break
      if node_found: break
      wall_color = img[j, y].tolist()
    # Check for edge in right direction
    for j in range(y + 1, height):
      if (img[x, j].tolist() == bg_color): break
      node_found = False
      for n2 in nodes:
        if (x, j) == n2:
          if (wall_color == outer_wall_color):
            horizontal_outer_edges.append((n, n2[1] - n[1]))
          elif (wall_color == wall_color):
            horizontal_inner_edges.append((n, n2[1] - n[1]))
          node_found = True
          break
      if node_found: break
      wall_color = img[x, j].tolist()

  #############################################################################################
  ### 5. Use the collected information to draw the final image, including doors and windows ###

  #Draw final walls with windows and doors
  for e in horizontal_inner_edges:
    #print("Horizontal edge draw from" + str(e[0]) + " to [" + str(e[0][0]) + ", " + str(e[0][1]+e[1]) + "]")
    for i in range(e[0][1], e[0][1] + e[1]):
      img[e[0][0], i] = horizontal_inner_wall_color
    #Draw doors
    if random.randint(0, 100) < inner_door_probability and e[1] > door_size:
      for i in range((e[0][1] + e[1] // 2) - door_size // 2,
                     (e[0][1] + e[1] // 2) + door_size // 2):
        img[e[0][0], i] = horizontal_door_color
  for e in vertical_inner_edges:
    #print("Vertical edge draw from" + str(e[0]) + " to [" + str(e[0][0]+e[1]) + ", " + str(e[0][1]) + "]")
    for i in range(e[0][0], e[0][0] + e[1]):
      img[i, e[0][1]] = vertical_inner_wall_color
    #Draw doors
    if random.randint(0, 100) < inner_door_probability and e[1] > door_size:
      for i in range((e[0][0] + e[1] // 2) - door_size // 2,
                     (e[0][0] + e[1] // 2) + door_size // 2):
        img[i, e[0][1]] = vertical_door_color

  for e in horizontal_outer_edges:
    #print("Horizontal edge draw from" + str(e[0]) + " to [" + str(e[0][0]) + ", " + str(e[0][1]+e[1]) + "]")
    for i in range(e[0][1], e[0][1] + e[1]):
      img[e[0][0], i] = horizontal_outer_wall_color
    #Draw door
    if random.randint(0, 100) < outer_door_probability and e[1] > door_size:
      for i in range((e[0][1] + e[1] // 2) - door_size // 2,
                     (e[0][1] + e[1] // 2) + door_size // 2):
        img[e[0][0], i] = horizontal_door_color
    #Draw 2 windows
    if e[1] > door_size + window_size * 3:
      if random.randint(0, 100) < window_probability:
        for i in range((e[0][1] + e[1] // 4) - window_size // 2,
                       (e[0][1] + e[1] // 4) + window_size // 2):
          img[e[0][0], i] = horizontal_window_color
      if random.randint(0, 100) < window_probability:
        for i in range((e[0][1] + (e[1] // 4) * 3) - window_size // 2,
                       (e[0][1] + (e[1] // 4) * 3) + window_size // 2):
          img[e[0][0], i] = horizontal_window_color
  for e in vertical_outer_edges:
    #print("Vertical edge draw from" + str(e[0]) + " to [" + str(e[0][0]+e[1]) + ", " + str(e[0][1]) + "]")
    for i in range(e[0][0], e[0][0] + e[1] + 1):
      img[i, e[0][1]] = vertical_outer_wall_color
    #Draw door
    if random.randint(0, 100) < outer_door_probability and e[1] > door_size:
      for i in range((e[0][0] + e[1] // 2) - door_size // 2,
                     (e[0][0] + e[1] // 2) + door_size // 2):
        img[i, e[0][1]] = vertical_door_color
    #Draw 2 windows
    if e[1] > door_size + window_size * 3:
      if random.randint(0, 100) < window_probability:
        for i in range((e[0][0] + e[1] // 4) - window_size // 2,
                       (e[0][0] + e[1] // 4) + window_size // 2):
          img[i, e[0][1]] = vertical_window_color
      if random.randint(0, 100) < window_probability:
        for i in range((e[0][0] + (e[1] // 4) * 3) - window_size // 2,
                       (e[0][0] + (e[1] // 4) * 3) + window_size // 2):
          img[i, e[0][1]] = vertical_window_color

  #Recolor rooms
  room_img = np.copy(img)
  for r in rooms:
    fill_bounds(room_img, r.x1, r.y1 + 1, r.x2 - 1, r.y2, r.color)
  
  #Prepare scaled images for all four versions
  cont_img = scale_image_nn(img, scale_factor)
  cont_room_img = scale_image_nn(room_img, scale_factor)
  symb_img = np.copy(cont_img)
  symb_room_img = np.copy(cont_room_img)

 
  ###############################
  ### 6. Apply plan symbology ###

  replace_color(cont_img, vertical_door_color, horizontal_door_color)
  replace_color(cont_img, vertical_window_color, horizontal_window_color)
  replace_color(cont_room_img, vertical_door_color, horizontal_door_color)
  replace_color(cont_room_img, vertical_window_color, horizontal_window_color)

  #Replace windows in both symbology plans
  windows = 0
  windows += replace_rectangles(symb_img, horizontal_window_color, "symbology/window_horizontal.png", 120, 30, 0, False, 0)
  windows += replace_rectangles(symb_img, vertical_window_color, "symbology/window_vertical.png", 30, 120, 0, True, 0)
  replace_rectangles(symb_room_img, horizontal_window_color, "symbology/window_horizontal.png", 120, 30, 0, False, 0)
  replace_rectangles(symb_room_img, vertical_window_color, "symbology/window_vertical.png", 30, 120, 0, True, 0)
  
  #Replace doors in both symbology plans
  doors = 0
  doors += replace_rectangles(symb_img, horizontal_door_color, "symbology/door_horizontal.png", 120, 120, 0.5, True, scale_factor)
  doors += replace_rectangles(symb_img, vertical_door_color, "symbology/door_vertical.png", 120, 120, 0.5, False, scale_factor)
  replace_rectangles(symb_room_img, horizontal_door_color, "symbology/door_horizontal.png", 120, 120, 0.5, True, scale_factor)
  replace_rectangles(symb_room_img, vertical_door_color, "symbology/door_vertical.png", 120, 120, 0.5, False, scale_factor)
  
  #Create description
  #Base
  desc = "floor plan of " + building_size(bounds_width, max_width, bounds_height, max_height) + "building"
  #Rooms
  desc += ", " + str(len(rooms)) + " rooms"
  #Windows
  if windows > 12:
    windows = "many"
  desc += ", " + str(windows) + " windows"
  #Doors
  if doors > 7:
    doors = "many"
  desc += ", " + str(doors) + " doors"
  #Deleted rooms
  #if(len(delete_list) > 0):
  #  desc += ", with courtyard"
  
  #Final output
  print("Image generated. Saving...")
  #Check if the image with symbology has colors or not. If it has, something went wrong.
  if not image_contains_color(symb_img):
    #plt.imsave("generations/" + str(random.randint(0, 999999)) + "-" + desc + ".png", scaled_img)
    plt.imsave("generations/symb/symb"+str(successfull_generations)+".png", symb_img)
    plt.imsave("generations/cont/cont"+str(successfull_generations)+".png", cont_img)
    plt.imsave("generations/symb_room/symb_room"+str(successfull_generations)+".png", symb_room_img)
    plt.imsave("generations/cont_room/cont_room"+str(successfull_generations)+".png", cont_room_img)	
    with open("generations/cont/cont"+str(successfull_generations)+".txt", 'w') as f:
      f.write(desc)
    with open("generations/symb/symb"+str(successfull_generations)+".txt", 'w') as f:
      f.write(desc)
    with open("generations/cont_room/cont_room"+str(successfull_generations)+".txt", 'w') as f:
      f.write(desc)
    with open("generations/symb_room/symb_room"+str(successfull_generations)+".txt", 'w') as f:
      f.write(desc)
    successfull_generations += 1
    print("Four images and description saved as number " + str(successfull_generations))
  else:
    print("Not saved, the symbology image had color.")
