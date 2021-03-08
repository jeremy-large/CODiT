import matplotlib.pyplot as plt
from matplotlib.animation import ArtistAnimation
import numpy as np


def setup_range_for_heatmap(pop, bin_num):
    """
    Establish range of all coordinates of the population's households for every heatmap generated later
    :param pop: population
    :param bin_num: bins size for histogram2d
    :return: range of all households coordinates on city map e.g. Leeds [-1.7776973000000003, -1.3100551999999999, 53.7060248, 53.942890000000006]
    """
    all_pop_coords = [[p.home.coordinate['lon'], p.home.coordinate['lat']] for p in pop.people if p.home is not None]
    if len(all_pop_coords) > 0:
        all_pop_coords_list = list(zip(*all_pop_coords))
        heatmap, xedges, yedges = np.histogram2d(all_pop_coords_list[0], all_pop_coords_list[1], bins=bin_num)
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    else:
        extent = [0, 0, 0, 0]
    return extent


class OutbreakVisualiser:

    def __init__(self, pop):
        # according to coordinates 'lon':'lat' ratio, the unit is inch, real size would fit the distribution
        self.plt = plt
        self.plt.rcParams["figure.figsize"] = [12, 5]
        self.fig = self.plt.figure(dpi=150)
        self.album_animation = []
        self.bin_num = max(int(300*len(pop.people)/1000000), 150)
        # set up heatmap range with all population's coordinates
        self.heatmap_range = setup_range_for_heatmap(pop, self.bin_num)

    def generate_heatmap(self, o):
        """
        Draw one heatmap of the infectious population for a specified time, and save it to camera
        :param o: instance of Outbreak
        :return:
        """
        if o.pop.count_infectious() > 0:
            coord = [[p.home.coordinate['lon'], p.home.coordinate['lat']] for p in o.pop.people if
                     p.infectious and (p.home is not None)]
            if len(coord) > 0:
                coord_column_list = list(zip(*coord))
                # param range in np.histogram2d: The leftmost and rightmost edges: [[xmin, xmax], [ymin, ymax]]
                # All values outside of this range will be considered outliers and not tallied in the histogram.
                heatmap, xedges, yedges = np.histogram2d(coord_column_list[0], coord_column_list[1], bins=self.bin_num,
                                                         range=[[self.heatmap_range[0], self.heatmap_range[1]],
                                                                [self.heatmap_range[2], self.heatmap_range[3]]])

                extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
                ax = self.plt.gca()
                vartext = ax.text(0.1, 1.02,
                        f'Day {int(o.time)}, prop infectious is {(o.pop.count_infectious() / len(o.pop.people)):2.4f} '
                        f'in simulated Leeds',
                        transform=ax.transAxes)

                self.plt.xlabel('latitude')
                self.plt.ylabel('longitude')
                self.album_animation.append([self.plt.imshow(heatmap.T, extent=extent, origin='lower', vmin=0, vmax=20),
                                             vartext])


    def show_heatmap_video(self, is_html5=False):
        """
        show heatmap_video in notebook
        :param is_html5:
        :return: H.264 video tag or jshtml video tag or (a string if no photos were taken)
        """
        if len(self.album_animation) > 0:
            animation = ArtistAnimation(self.fig, self.album_animation, interval=1000, repeat=False)
            if is_html5:
                return animation.to_html5_video()
            else:
                return animation.to_jshtml()
        else:
            return "no heatmap to show!"

    def close_plt(self):
        """
        close plt after cameras have been saved to avoid showing single heatmap
        :return:
        """
        self.plt.close()


class VisualizerComponent:
    def __init__(self, is_html5, o):
        self.is_html5 = is_html5
        self.visualiser = OutbreakVisualiser(o.pop)

    def outbreak_visualise(self, is_html5=False):
        """
        show heatmap_video in notebook
        :return: video tag or a string
        """
        if self.visualiser:
            return self.visualiser.show_heatmap_video(is_html5)
        else:
            return "Video has been switched off!"

    def update(self, o):
        if self.visualiser:
            if o.step_num % (7 * o.society.episodes_per_day) == 1 or (o.step_num == o.n_periods):
                self.visualiser.generate_heatmap(o)
                if o.step_num == o.n_periods:
                    self.visualiser.close_plt()
