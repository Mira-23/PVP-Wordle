# import pygame

random_word = "batch"
letters = list(random_word)

count = 0

def is_word_valid(word: str) -> bool:
    if word:
        return True
    else:
        return False

while count!=6:

    guess = input()
    if not is_word_valid(guess):
        continue

    count+=1
    pass



print("damn, you lost!")

# pygame.init()

# screen = pygame.display.set_mode((640,640))
# clock = pygame.time.Clock()
# delta_time = 0.1

# running = True
# while running:
#     #white background
#     screen.fill((255,255,255))

#     #closing the window
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     #display stuff on the window
#     pygame.display.flip()

#     #time handling for framerate
#     delta_time = clock.tick(60) / 1000
#     delta_time = max(0.001, min(0.1,delta_time))

# pygame.quit()