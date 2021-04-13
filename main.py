import numpy as np
import pandas as pd
from numpy.random import default_rng
import pygame

rng = default_rng()


class City:
    infected_number = 0
    new_case = 0
    day = 0
    population_number = 0
    recovered = 0
    dead = 0

    def __init__(self, population_number):
        self.population_number = population_number
        self.city = pd.DataFrame(
            {
                'age': rng.integers(0, 91, size=population_number, dtype='int8'),
                'is_infected': 0,
                'day_since_infected': 0,
                'contact': rng.normal(5.2, 1.4, size=population_number).astype('int8'),
                'contagion_level': rng.integers(95, 101, size=population_number, dtype='int8'),
                'contagious': 0,
                'dead': 0,
            },
            pd.RangeIndex(start=0, stop=population_number), dtype='int8')

    def create_cluster(self):
        sample = rng.integers(0, self.population_number, size=5, dtype='int32')

        self.city['is_infected'] = np.select([self.city.index.isin(sample)],
                                             [self.city['is_infected'].values + 1],
                                             self.city['is_infected'])

        self.infected_number += (self.city['is_infected'].values == 1).sum()

    def update(self):
        self.city['dead'] = np.select([(self.city['dead'].values == 2), (self.city['dead'].values == 1)],
                                      [3, 4],
                                      self.city['dead'].values)

        # random number for each person will be used for death probability ///
        self.city['probability'] = rng.integers(0, 101, size=self.population_number, dtype='int8')

        # update day_since_infected ///
        self.city['day_since_infected'] = np.select([(self.city['is_infected'].values == 1) &
                                                     (self.city['day_since_infected'].values < 20)],
                                                    [self.city['day_since_infected'].values + 1],
                                                    self.city['day_since_infected'].values)

        # update last day of contagion ///
        # dead = 1 mean dead
        # dead = 2 mean survived to the virus

        condition_dead = [
            (self.city['age'].values < 30),
            ((self.city['age'].values > 80) & (self.city['probability'].values > 79)),
            ((self.city['age'].values > 70) & (self.city['probability'].values > 89)),
            ((self.city['age'].values > 60) & (self.city['probability'].values > 96)),
            ((self.city['age'].values > 30) & (self.city['probability'].values > 98)),
        ]

        self.city['dead'] = np.where(self.city['day_since_infected'].values == 18,
                                     np.select(condition_dead, [2, 1, 1, 1, 1],
                                               2), self.city['dead'])
        # not infected anymore is_infected = 2
        self.city['is_infected'] = np.select([self.city['day_since_infected'].values == 18],
                                             [2],
                                             self.city['is_infected'].values)
        # reset day_since_infected
        self.city['day_since_infected'] = np.select([self.city['day_since_infected'].values == 18],
                                                    [0],
                                                    self.city['day_since_infected'].values)

        # update contagious state ///
        self.city['contagious'] = np.select([(self.city['day_since_infected'].values == 18),
                                             (self.city['day_since_infected'].values > 1)],
                                            [0, 1],
                                            self.city['contagious'].values)

        # contagion update ///
        # create shift values for each person to translate the proximity of the contact in the graphic representation
        # the person's contacts will mainly be located in a square arround her in the graphic representation
        shiftx = rng.normal(0, 10, size=10)
        shiftx = np.select([((shiftx > 0) & (shiftx < 1)), ((shiftx < 0) & (shiftx > -1))], [1, -1],
                           np.round(shiftx).astype('int8'))
        shifty = rng.normal(0, 10, size=10)
        shifty = np.select([((shifty > 0) & (shifty < 1)), ((shifty < 0) & (shifty > -1))], [1, -1],
                           np.round(shifty).astype('int8'))
        shifty = shifty * 1000

        condition = [
            (self.city['contagious'].shift(1).values == 1) & (
                self.city['probability'].values > self.city['contagion_level'].shift(
                    shiftx[0] + shifty[0]).values)]

        for i in range(9):
            condition += [(self.city['contact'].values > i) & (
                self.city['contagious'].shift(shiftx[i] + shifty[i]).values == 1) & (
                self.city['probability'].values > self.city['contagion_level'].shift(
                    shiftx[i] + shifty[i]).values)]
        
        # check if the non infected person get infected by one of his contact
        self.city['is_infected'] = np.where(self.city['is_infected'].values == 0,
                                            np.select(condition, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 0),
                                            self.city['is_infected'].values)

        # update stats ///
        self.new_case = ((self.city['is_infected'].values == 1) & (self.city['day_since_infected'] == 0)).sum()
        self.infected_number = (self.city['is_infected'].values == 1).sum()
        self.recovered += (self.city['dead'].values == 2).sum()
        self.dead += (self.city['dead'].values == 1).sum()


def main():
    test = City(1_000_000)
    test.create_cluster()
    pygame.init()
    draw = True
    screen = pygame.display.set_mode((1000, 1000))
    pygame.display.set_caption("Virus spread simulation")

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))

    screen.blit(background, (0, 0))
    pygame.display.flip()
    myfont = pygame.font.SysFont('Comic Sans MS', 10)

    while draw:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                draw = False
        test.new_case = 0
        test.day += 1
        test.update()

        infected = (test.city['day_since_infected'][(test.city['is_infected'].values == 1) &
                                                    (test.city['day_since_infected'] == 0)]).index
        
        # translate the dataframe index to a pixel coordinate
        for i in infected:
            xi = round(((i / 1000) % 1) * 1000)
            yi = i // 1000
            screen.set_at((xi, yi), pygame.color.Color('red'))

        dead = (test.city['dead'][test.city['dead'].values == 1]).index
        for j in dead:
            xj = round(((j / 1000) % 1) * 1000)
            yj = j // 1000
            screen.set_at((xj, yj), pygame.color.Color('black'))

        recovered = (test.city['dead'][test.city['dead'].values == 2]).index
        for k in recovered:
            xk = round(((k / 1000) % 1) * 1000)
            yk = k // 1000
            screen.set_at((xk, yk), pygame.color.Color('green'))

        text_day = myfont.render("Day : " + str(test.day), True, (0, 0, 0), (250, 250, 250))
        text_infected = myfont.render("Infected : " + str(test.infected_number), True, (0, 0, 0), (250, 250, 250))
        text_death_rate = myfont.render("Death rate : " + str(round(test.dead / test.population_number * 100, 2)) + "%",
                                        True,
                                        (0, 0, 0), (250, 250, 250))
        text_recovered = myfont.render("Recovered : " + str(test.recovered), True, (0, 0, 0), (250, 250, 250))
        text_dead = myfont.render("Dead : " + str(test.dead), True, (0, 0, 0), (250, 250, 250))

        screen.blit(text_day, (5, 5))
        screen.blit(text_infected, (5, 18))
        screen.blit(text_death_rate, (5, 31))
        screen.blit(text_recovered, (5, 44))
        screen.blit(text_dead, (5, 57))

        pygame.display.update()


main()
