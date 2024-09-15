import csv
import logging
import random
import time
import os

import pygame
import matplotlib
import matplotlib.backends.backend_agg as agg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from car import Car
import config as c


matplotlib.use('Agg')
matplotlib.use('PS')
random.seed(175175175)
np.random.seed(175175175)


TOTAL_SIMULATIONS = 15
PIXEL_METERS_RATIO = 0.04
PPU = 30
SIMULATION_TIME = 30
DT = 0.1
TIME_THRESHOLD = 15
DATA_FILE_FLOW = "data/flow_density_data.csv"
DATA_FILE_SPEED = "data/speed_density_data.csv" 


class Environment:
    def __init__(self, args):
        self.render = not args.no_render
        
        if args.run_idm:
            self.model = 'IDM'
        elif args.run_custom:
            self.model = 'Custom'
        else:
            self.model = 'Test'

        if self.render:
            # initialize the interfaces
            pygame.init()
            pygame.display.set_caption(c.PROJECT_NAME)
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.exit = False
            info_object = pygame.display.Info()
            logging.info("Created info_object...")
            self.screen_width = info_object.current_w
            logging.info("Set screen_width...")
        else:
            # A dummy screen width to bypass pygame
            self.screen_width = 1000

        self.file_fd = open(DATA_FILE_FLOW, "w")
        flow_data_fieldnames = ['density', 'flow']
        self.writer_fd = csv.DictWriter(self.file_fd, fieldnames=flow_data_fieldnames)
        self.writer_fd.writeheader()
        self.file_sd = open(DATA_FILE_SPEED, "w")
        speed_data_fieldnames = ['density', 'speed']
        self.writer_sd = csv.DictWriter(self.file_sd, fieldnames=speed_data_fieldnames)
        self.writer_sd.writeheader()
        
        # Load the graphs
        self.figure_svd, self.figure_fvd, self.axis_svd, self.axis_fvd = self.init_graphs()
        self.vehicle_counts = np.random.permutation(np.array([1,2,2,4,7,11,15,18,21,24,30,40,60,80,99]))
        self.simulation_count = 0
        self.trajectory = []  # Trajectory recording the tuple of (car,time,position)

    @staticmethod
    def init_graphs():
        # initialize the graphs
        figure_svd, axis_svd = plt.subplots()
        figure_fvd, axis_fvd = plt.subplots()
        
        axis_svd.plot([], [])
        axis_fvd.plot([], [])

        axis_svd.set(xlabel='Density (veh/m)', ylabel='Speed (m/s)', title='Speed vs Density')
        axis_fvd.set(xlabel='Density (veh/m)', ylabel='Flow (veh/s)', title='Flow vs Density')

        axis_svd.grid()
        axis_fvd.grid()

        return figure_svd, figure_fvd, axis_svd, axis_fvd


    def plot_graph(figure):
        # Generate figure structure on the canvas
        canvas = agg.FigureCanvasAgg(figure)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()

        size = canvas.get_width_height()

        return raw_data, size
        

    @staticmethod
    def plot_fundamental_diagrams():
        flow_data = pd.read_csv(DATA_FILE_FLOW)
        figure_svd, figure_fvd, axis_svd, axis_fvd = Environment.init_graphs()
        axis_fvd.scatter(flow_data['density'], flow_data['flow'])
        figure_fvd.savefig('figures/fundamental_diagram_flow_vs_density.png')

        speed_data = pd.read_csv(DATA_FILE_SPEED)
        axis_svd.scatter(speed_data['density'], speed_data['speed'])
        figure_svd.savefig('figures/fundamental_diagram_speed_vs_density.png')

    
    def clean_up(self):
        # Close file descriptors for writing data files
        self.file_fd.close()
        self.file_sd.close()

        # Save the trajectory data of the IDM model for separate analysis
        if self.model == "IDM":
            df_trajectory = pd.DataFrame(self.trajectory, columns = ['Simulation No','Car', 'Time', 'Position'])
            df_trajectory.to_csv('data/trajectory.csv')


    def run(self):
        # load car image for the visualization
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "assets/car.png")
        screen_width = self.screen_width
        if self.render:
            car_image = pygame.image.load(image_path)

        svd_x_axis = []
        svd_y_axis = []
        fvd_x_axis = []
        fvd_y_axis = []

        while self.simulation_count < TOTAL_SIMULATIONS:

            self.simulation_count += 1
            time_elapsed = 0
            cars = []

            num_vehicles = self.vehicle_counts[self.simulation_count-1]

            for x in range(0, num_vehicles):
                if x == 0:
                    cars.append(Car((screen_width / PPU - (48 / PPU)) * 0.75, 2, x, screen_width))
                else:
                    cars.append(Car(cars[x - 1].position.x - random.uniform(1, 2), 2, x, screen_width))

            reference_position_x = cars[len(cars) - 1].position.x - 1
            road_length = max((screen_width / PPU - (48 / PPU)) * 0.25,
                              (abs(screen_width / PPU - (48 / PPU)) - reference_position_x))
            info_string = f'Running {self.model} Simulation No. {self.simulation_count:>2d} with ' \
                f'{num_vehicles:>2d} vehicles and road length of {road_length:>3.0f} meters.'
            logging.info(info_string)
            density = num_vehicles / (road_length * PIXEL_METERS_RATIO)

            flow = 0
            sum_velocity = 0
            velocity_count = 0

            while SIMULATION_TIME > time_elapsed:

                time_elapsed += DT
                car_previous_positions_x = []

                # Update each vehicle's status
                for x,_ in enumerate(cars):
                    if x == 0:
                        car_previous_positions_x.append(cars[0].position.x)
                        cars[x].car_following_model(DT, cars[len(cars) - 1], cars[min(len(cars)-1, 1)],
                        reference_position_x, self.model)
                    elif x < len(cars) -1:
                        car_previous_positions_x.append(cars[x].position.x)
                        cars[x].car_following_model(DT, cars[x - 1], cars[x + 1], reference_position_x, self.model)
                    else:
                        car_previous_positions_x.append(cars[x].position.x)
                        cars[x].car_following_model(DT, cars[x - 1], cars[0], reference_position_x, self.model)
                    self.trajectory.append((self.simulation_count, x,time_elapsed, cars[x].position.x))

                if time_elapsed > TIME_THRESHOLD:
                    for y,_ in enumerate(cars):
                        if cars[y].position.x < car_previous_positions_x[y]:
                            flow += 1

                if time_elapsed > TIME_THRESHOLD:
                    for car in cars:
                        sum_velocity += car.velocity.x
                        velocity_count += 1

                if self.render:
                    # Event queue for the simulation
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.exit = True
                        if event.type == pygame.KEYDOWN:
                            # Quit the simulation whenever a key is pressed
                            self.clean_up()
                            self.plot_fundamental_diagrams()
                            pygame.quit()
                            return

                    # Draw the simulation interface
                    self.screen.fill((255, 255, 255))
                    rotated = pygame.transform.rotate(car_image, 0)

                    for x,_ in enumerate(cars):
                        self.screen.blit(rotated, cars[x].position * PPU)

                    screen = pygame.display.get_surface()

                    # Draw the svd graph
                    svd_raw_data, svd_size = Environment.plot_graph(self.figure_svd)
                    surf = pygame.image.fromstring(svd_raw_data, svd_size, "RGB")
                    screen.blit(surf, (screen_width / 9, 180))

                    # Draw the fvd graph
                    fvd_raw_data, fvd_size = Environment.plot_graph(self.figure_fvd)
                    surf = pygame.image.fromstring(fvd_raw_data, fvd_size, "RGB")
                    screen.blit(surf, (screen_width / 2, 180))

                    # Add text to interface
                    font = pygame.font.Font('freesansbold.ttf', 16)
                    text = font.render(info_string, True, (0, 0, 0), (255, 255, 255))
                    text_quit = font.render('[X] : Press any key to quit the simulation.',
                                    True, (0, 0, 0), (255, 255, 255))

                    text_rect = text.get_rect()
                    text_rect_quit = text_quit.get_rect()
                    text_rect.center = (400, 25)
                    text_rect_quit.center = (400, 50)
                    screen.blit(text, text_rect)
                    screen.blit(text_quit, text_rect_quit)

                    # Update interface
                    pygame.display.flip()

            # collect data relevant for plotting
            avg_velocity = sum_velocity / velocity_count
            self.writer_sd.writerow({'density': density, 'speed': avg_velocity})

            flow_real = flow / (SIMULATION_TIME - TIME_THRESHOLD)
            self.writer_fd.writerow({'density': density, 'flow': flow_real})

            svd_x_axis.append(density)
            svd_y_axis.append(avg_velocity)
            self.axis_svd.scatter(svd_x_axis, svd_y_axis)

            fvd_x_axis.append(density)
            fvd_y_axis.append(flow_real)
            self.axis_fvd.scatter(fvd_x_axis, fvd_y_axis)

        self.clean_up()
        self.plot_fundamental_diagrams()

        if self.render:
            # Wait 5 seconds before closing the display
            time.sleep(5)
