import os
import sys
import time

import numpy as np
import json

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener

sys.path.append(os.path.abspath(".."))

from flowcontrol.strategy.controller.dummy_controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.utils.misc import get_scenario_file

from shapely.geometry import Polygon, Point

import pandas as pd
import matplotlib.pyplot as plt

working_dir = dict()
PRECISION = 8


class NoController(Controller):
    def __init__(self):
        super().__init__()
        print("Dummy controller.")

        self.density_over_time = list()
        self.time_step = list()
        self.sensor_time_step_size = 0.4
        self.corridor_choice_over_time = list()
        self.next_call = 0
        self.time_step_size = 10

    def handle_sim_step(self, sim_time, sim_state):

        self.measure_state(sim_time)

        # necessary, because time intervals for sensoring and applying a control action differ
        if (sim_time-self.sensor_time_step_size) % self.time_step_size == 0:
            self.compute_next_corridor_choice(sim_time)
            self.apply_redirection_measure()

        self.next_call += self.sensor_time_step_size
        self.con_manager.next_call_at(self.next_call)

    def measure_state(self, sim_time):

        peds1 = self.con_manager.sub_listener["default"].pedestrians
        density = list()

        # TODO: replace this for loop by 'get_density_measure_from_density_map'
        #   density = self.con_manager.domains.v_sim.get_density_map()
        #         sending_node = "pNode[1].densityMap.app"
        #         density_map = self.con_manager.domains.v_sim.get_density_map(sending_node)
        for a in self.measurement_areas:
            counts = len(
                [p["id"] for p in peds1 if a.contains(Point(p["pos"][0], p["pos"][1]))]
            )
            density.append(counts / a.area)

        time_step = (
            np.round(sim_time / self.sensor_time_step_size, 0) + 1
        )  # time = 0.0s := timestep 1, time step size: 0.4

        # print(f"Sim-time: {sim_time}, timeStep: {time_step}) \t Density measured: {density}")
        self.density_over_time.append(density)
        self.time_step.append(time_step)

    def apply_redirection_measure(self):
        pass

    def handle_init(self, sim_time, sim_state):
        self.counter = 0
        self.con_manager.next_call_at(0.4)
        self.measurement_areas = self._get_measurement_areas([1, 2, 3, 4, 5])
        self.measure_state(0.0)

    def check_density_measures(self):
        self.measure_state(self.next_call + self.sensor_time_step_size)
        index = pd.Index(data=self.time_step, name="timeStep", dtype=int)
        densities = pd.DataFrame(
            data=np.array(self.density_over_time),
            columns=[f"areaDensityCountingNormed-PID{x}" for x in [14, 15, 16, 17, 18]],
            index=index,
        ).round(PRECISION)

        density_file = os.path.join(working_dir["path"], "densities.txt")
        while os.path.isfile(density_file) is False:
            time.sleep(1)
        time.sleep(1)
        
        dens_check = (
            pd.read_csv(
                density_file,
                delimiter=" ",
                index_col=[0],
            )
            .sort_index(axis=1)
            .round(PRECISION)
        )
        if densities.equals(dens_check) is False:

            if densities[:-1].equals(dens_check[:-1]) is False:
                raise ValueError(
                    "Densities from data processors do not equal THESE densities."
                )
            else:
                print(
                    "INFO: Simulation time might differ for last time step. Skipped time step in comparison."
                )

    def _get_measurement_areas(self, measurement_area_ids):
        areas = list()
        for measurement_id in measurement_area_ids:
            polygon = self.con_manager.domains.v_polygon.get_shape(str(measurement_id))
            polygon_ = Polygon(np.array(polygon))
            areas.append(polygon_)

        return areas

    def collect_data(self):

        self.check_density_measures()
        self.plot_densities()

    def plot_densities(self):

        densities = pd.read_csv(
            os.path.join(working_dir["path"], "densities.txt"),
            delimiter=" ",
            index_col=[0],
        )

        dataprocessor_name_density = "areaDensityCountingNormed-PID"
        corridor_name = "Corridor"
        dataprocessormapping_density = {
            f"{dataprocessor_name_density}14": f"{corridor_name} 1",  # shortest path
            f"{dataprocessor_name_density}15": f"{corridor_name} 2",
            f"{dataprocessor_name_density}16": f"{corridor_name} 3",
            f"{dataprocessor_name_density}17": f"{corridor_name} 4",
            f"{dataprocessor_name_density}18": f"{corridor_name} 5",  # longest path
        }
        cut = 250
        # densities
        densities = densities.iloc[cut : cut + 1000, :]
        densities.rename(columns=dataprocessormapping_density, inplace=True)
        densities.sort_index(axis=1, inplace=True)

        densities.plot()
        plt.legend(loc='upper left')
        densities.index = densities.index * self.sensor_time_step_size
        plt.xlim([0, self.sensor_time_step_size*(cut+1000)])
        plt.xlabel("Simulation time [s]")
        plt.ylabel("Density [1/m^2]")
        plt.title(f"Density over time")
        plt.ylim([0, 2])
        plt.legend()
        plt.savefig(os.path.join(working_dir["path"], f"{os.path.basename(working_dir['path'])}_density_over_time.png"))
        plt.show(block=False)
        plt.close()

        densities.boxplot()
        plt.ylabel("Density [1/m^2]")
        plt.title(
            f"Number of pedestrians (sample size = {len(densities)})"
        )
        plt.ylim([0, 2])
        plt.savefig(os.path.join(working_dir["path"], f"{os.path.basename(working_dir['path'])}_density_distribution.png"))
        plt.show(block=False)
        plt.close()

    def compute_next_corridor_choice(self, sim_time):
        pass

    def set_reaction_model_parameters(self, reaction_probability):
        pass


class OpenLoop(NoController, Controller):
    def __init__(self):
        super().__init__()
        self.target_ids = [11, 21, 31, 41, 51]
        self.redirected_agents = list()
        self.controlModelType = "RouteChoice"
        self.controlModelName = "distributePeds"
        self.commandID = 111

        self.reaction_model = {
            "isBernoulliParameterCertain": True,
            "BernoulliParameter": 1.0,
        }


    def collect_data(self):

        self.check_density_measures()
        self.path_choice()
        self.plot_densities()


    def apply_redirection_measure(self):

        probabilities = [0, 0, 0, 0, 0]
        probabilities[self.counter] = 1.0 # all of the agents should use one specific corridor

        command = {"targetIds": self.target_ids, "probability": probabilities}
        action = {
            "commandId": self.commandID,
            "command": command,
            "space": {"x": 0.5, "y": 0.5, "width": 5, "height": 15}, # get information direclty after spawning process
        }
        action = json.dumps(action)
        self.commandID += 1
        self.con_manager.domains.v_sim.send_control(message=action, model=self.controlModelName)


    def _increase_counter(self):
        self.counter += 1
        self._reset_counter()

    def _reset_counter(self):
        if self.counter >= len(self.target_ids):
            self.counter = 0

    def compute_next_corridor_choice(self, sim_time):

        old_counter = self.counter

        self.choose_corridor()

        print(f"Use corridor {self.target_ids[self.counter]}.")

        self.corridor_choice_over_time.append([sim_time, old_counter, self.counter])

    def choose_corridor(self):
        self._increase_counter()

    def path_choice(self):

        corridor_corrections = pd.DataFrame(
            data=np.array(self.corridor_choice_over_time),
            columns=["timeStep", "OldCorridor", "NewCorridor"],
        )
        corridor_corrections.set_index("timeStep", inplace=True)
        corridor_corrections.to_csv(
            os.path.join(working_dir["path"], "path_choice.txt")
        )

        plt.scatter(
            corridor_corrections.index.to_numpy(),
            corridor_corrections["NewCorridor"] + 1,
        )
        plt.ylim([0.5, 5.5])
        plt.xlim([0, 500])
        plt.yticks([1, 2, 3, 4, 5])
        plt.xlabel("Simulation time [s]")
        plt.ylabel("Corridor recommendation")
        plt.savefig(os.path.join(working_dir["path"], f"{os.path.basename(working_dir['path'])}_path_choice.png"))
        plt.show(block=False)
        plt.close()

    def get_reaction_model_parameters(self):
        return json.dumps(
          self.reaction_model
        )

    def set_reaction_model_parameters(self, reaction_probability):
        self.reaction_model["BernoulliParameter"] = reaction_probability



    def handle_init(self, sim_time, sim_state):
        self.con_manager.domains.v_sim.init_control(
            self.controlModelName, self.controlModelType, self.get_reaction_model_parameters()
        )
        super().handle_init(sim_time, sim_state)


class ClosedLoop(OpenLoop, Controller):
    def __init__(self):
        super().__init__()

    def choose_corridor(self):
        # measure densities in corridors
        # average densities between two controller calls
        number_of_time_steps_for_measurement = int(
            np.round(self.time_step_size / self.sensor_time_step_size, 0)
        )
        densities = np.array(
            self.density_over_time[-number_of_time_steps_for_measurement:]
        ).mean(axis=0)
        # set old corridor to inf to avoid congestion:
        densities[self.counter] = np.inf
        self.counter = np.argwhere(densities == densities.min()).ravel()[-1]

        print(
            f"The densities are: {densities.round(3)}. Minimum: index = {self.counter}."
        )


def main(
    settings, controller_type="OpenLoop", scenario="simplified_default_sequential", reaction_probability=1.0
):

    sub = VadereDefaultStateListener.with_vars(
        "persons", {"pos": tc.VAR_POSITION}, init_sub=True,
    )

    scenario_file = get_scenario_file(f"vadere/scenarios/{scenario}.scenario")
    kwargs = {
        "file_name": scenario_file,
    }

    working_dir["path"] = os.path.join(os.getcwd(), f"{scenario}_{controller_type}_prob_{int(reaction_probability)}")

    settings_ = settings
    settings_.extend(["--output-dir", working_dir["path"]])
    settings_.extend(["--controller-type", controller_type])

    controller = get_controller_from_args(working_dir=os.getcwd(), args=settings_)
    controller.register_state_listener("default", sub, set_default=True)
    controller.set_reaction_model_parameters(reaction_probability=reaction_probability)
    controller.start_controller(**kwargs)


if __name__ == "__main__":

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "localhost",
            "--client-mode",
            "--start-server",
            "--gui-mode",
            "--path-to-vadere-repo",
            os.path.abspath("../../../vadere"),
            "--suppress-prompts",
        ]

        main(
            settings,
            controller_type="NoController",
            scenario="simplified_default_sequential",
        )
        main(
            settings,
            controller_type="OpenLoop",
            scenario="simplified_default_sequential",
        )
        main(
            settings,
            controller_type="ClosedLoop",
            scenario="simplified_default_sequential",
        )
        main(
            settings,
            controller_type="OpenLoop",
            scenario="simplified_default_sequential",
            reaction_probability=0.5
        )
        main(
            settings,
            controller_type="ClosedLoop",
            scenario="simplified_default_sequential",
            reaction_probability=0.5
        )
        main(
            settings,
            controller_type="OpenLoop",
            scenario="simplified_default_sequential_disturbance",
        )
        main(
            settings,
            controller_type="ClosedLoop",
            scenario="simplified_default_sequential_disturbance",
        )

    else:
        settings = sys.argv[1:]
