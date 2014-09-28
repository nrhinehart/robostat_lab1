import math, copy, os
import numpy
import numpy as np
import pdb
import gtkutils.img_util as iu
from gtkutils.color_printer import gcp

class map_obj(object):
    def __init__(self, map_fn):
        x = 0
        self.hit_thresh = 0.8

        self.coord_idx_lookup = {}

        self.valid_coordinates = []
        for line in open(map_fn, 'r').readlines():
            line = line.rstrip().split()
            if (len(line) == 0):
                continue
            elif (line[0] == 'robot_specifications->global_mapsize_x'):
                pass
            elif (line[0] == 'robot_specifications->global_mapsize_y'):
                pass
            elif (line[0] == 'robot_specifications->resolution'):
                self.resolution = int(line[1])
            elif (line[0] == 'robot_specifications->autoshifted_x'):
                pass
            elif (line[0] == 'robot_specifications->autoshifted_y'):
                pass
            elif (line[0] == 'global_map[0]:'):
                self.mapsize_x = int(line[1])
                self.mapsize_y = int(line[2])
                self.grid = np.zeros((self.mapsize_x, self.mapsize_y), dtype=np.float64)
            else:
                # read 800 occupancy cells. 
                # update self.grid
                for y in range(self.mapsize_y):
                    self.grid[x, y] = np.float64(line[y])
                    if not self.is_hit((x, y), is_pose = False):
                        idx = len(self.valid_coordinates)
                        self.valid_coordinates.append((x, y))
                        self.coord_idx_lookup[(x, y)] = idx
                x += 1

        self.grid[self.grid == -1] = 0
        self.hit_map = self.grid <= self.hit_thresh
        self.free_map = 1 - self.hit_map 

        assert(len(self.valid_coordinates) > 0)

        self.n_angle_bins = 36
        self.angle_bins_step = 2 * numpy.pi / self.n_angle_bins        
        rays_fn = 'preprocessed_rays_{}_{}.npz'.format(self.n_angle_bins,
                                                       os.path.basename(map_fn))

        if not os.path.isfile(rays_fn) or 1:
            gcp.gtime(self.preprocess_rays)
            numpy.savez_compressed(rays_fn, self.ray_lookup)
        else:
            self.ray_lookup = numpy.load(rays_fn)['arr_0']


        #iterate over positions in the map,
        #if it's valid add to valid coordinates
        # self.valid_coordinates.append(xy(x, y))

    def get_pose_coord(self, pose):
        return (int(pose[0] / self.resolution + .5), int(pose[1] / self.resolution + .5))

    def show(self):
        iu.v((self.grid + 1.0) / 2.0)

    def show_hit_map(self):
        iu.v(self.hit_map)

    def get_valid_coordinates(self):
      return self.valid_coordinates

    def is_hit(self, pose, is_pose = True):
        if is_pose:
            pose_coord = self.get_pose_coord(pose)
        else:
            pose_coord = (int(pose[0] + .5), int(pose[1] + .5))

        if 0 <= pose_coord[0] < self.grid.shape[0] and \
           0 <= pose_coord[1] < self.grid.shape[1]:
            p = self.grid[pose_coord[0], pose_coord[1]]
            return p <= self.hit_thresh
        return True

    def ray_finding(self, pose, is_pose = True):
        mult_const = 1
        inc = mult_const if is_pose else mult_const / float(self.resolution)

        pose = copy.deepcopy(pose)
        pose_delt = inc * numpy.array((math.cos(pose[2]), math.sin(pose[2]), 0.0))
        dist = 0
        is_hit = self.is_hit(pose, is_pose = is_pose)
        while not is_hit:
            pose += pose_delt
            dist += mult_const
            is_hit = self.is_hit(pose, is_pose = is_pose)
        return dist

    def preprocess_rays(self):
        self.ray_lookup = numpy.zeros((len(self.valid_coordinates),
                                       self.n_angle_bins), dtype = numpy.float64)

        # assumes all poses are [0, 2pi)
        for (c_idx, coord) in enumerate(self.valid_coordinates):
            if c_idx % 20 == 0:
                print c_idx, len(self.valid_coordinates)
            for (a_idx, angle) in enumerate(numpy.arange(0, 2*numpy.pi, self.angle_bins_step)):
                pose = numpy.array([coord[0], coord[1], angle])
                dist = self.ray_finding(pose, is_pose = False)
                if (dist == 0): 
                    print "dist is 0..."
                    pdb.set_trace()
                self.ray_lookup[c_idx, a_idx] = dist

    def vis_ray_lookup(self, r_idx):
        hm = self.hit_map.copy()
        canvas = 255 * numpy.dstack((numpy.zeros_like(hm), hm, hm)).astype('uint8')
        
        dists = self.ray_lookup[r_idx, :]
        angles = numpy.arange(0, 2*numpy.pi, self.angle_bins_step)

        coords = []
        start_coord = self.valid_coordinates[r_idx]
        
        color = [255, 0, 0]
        canvas[start_coord[0], start_coord[1], :] = [0, 255, 0]

        for angle_idx in range(self.ray_lookup.shape[1]):
            angle = angles[angle_idx]
            dist = dists[angle_idx]

            pose_delt = dist * numpy.array((math.cos(angle), math.sin(angle), 0.0)) / self.resolution
            print pose_delt
            new_coord = map(int, [start_coord[0] + pose_delt[0],
                                  start_coord[1] + pose_delt[1]])
            canvas[new_coord[0], new_coord[1], :] = color

        canvas[start_coord[0], start_coord[1], :] = [0, 255, 0]

        iu.v(canvas)
            

            
            
            
                        
            
