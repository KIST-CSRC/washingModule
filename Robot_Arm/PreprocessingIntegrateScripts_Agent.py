import os
import sys
import time
from enum import Enum, auto

# --- Import path setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "/LabWare")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "/LabWare/Pump"))
)

from Robot_Arm.PreprocessRoboticArm import *
from LabWare.Arduino.Centri_LA import Centri_LA
from LabWare.Arduino.Centrimodule import CentrifugeManager
from LabWare.Arduino.DeskLA import DeskLA
from LabWare.Arduino.DispenserLA import DispenserLA
from LabWare.Pump.Nextpump_3ea import Next3000FJ, NextPumpParemter
from LabWare.Pump.Preprocess_Xcaliburd import XCaliburD
from LabWare.UltraSonic.Sonic_Class import SonorexDigitec
from TCP import TCP_Class
from Log.Logging_Class import NodeLogger

# Import LLM module
from WashingLLM.Assistant_Based_RAG import WashingMethodRetrival, RecipeGenerator


class WashingTask:
    def __init__(self, logger, recipe):
        # --- Logger initialization ---
        self.logger = logger

        # --- Recipe initialization ---
        self.recipe = recipe
        self.batch_size = self.recipe["metadata"].get("BatchSize", 1)
        self.transfer_liquid_volume = self.recipe["metadata"].get("TransferLiquid", 1)
        self.mode_type = self.recipe["metadata"].get("mode_type", "virtual")
        self.solvents = self.recipe["process"].get("Solvents", [])
        self.volumes = self.recipe["process"].get("Solvents_Volume", [])
        self.centri_time = self.recipe["process"].get("CentrifugationTime", 0)
        self.centri_speed = self.recipe["process"].get("CentrifugationRPM", 0)
        self.sonic_set_time = self.recipe["process"].get("sonic_set_time", 0)

        # --- Hardware components ---
        self.centri_obj = Centri_LA(self.logger)
        self.deskla_obj = DeskLA(self.logger)
        self.dispenser_obj = DispenserLA(self.logger)
        self.tcp_obj = TCP_Class()
        self.sonic_obj = SonorexDigitec(self.logger)
        self.Centrimanager = CentrifugeManager(self.logger)
        self.param_pump_obj = NextPumpParemter()
        self.pumps = self._initialize_pumps()
        self.remove_liquid_pump = self.pumps.get("Remove")

        openGripper(action_type="Falcon")

        # --- Device configuration (example setup) ---
        self.device_config = {
            "Ethanol": {"solution_name": "Ethanol", "tecan_addr": 1},
            "Acetone": {"solution_name": "Acetone", "tecan_addr": 2},
            "H2O": {"solution_name": "H2O", "tecan_addr": 5},
        }

        self.devices = {}
        for device_name in self.device_config:
            if device_name == "XcaliburD":
                self.devices[device_name] = XCaliburD(
                    self.logger, device_name=device_name
                )

    def _initialize_pumps(self):
        """Initialize pump instances based on parameter configuration."""
        pumps = {}
        param_info_dict = self.param_pump_obj.info
        for solvent_type, pump_info in param_info_dict.items():
            pumps[solvent_type] = Next3000FJ(
                logger_obj=self.logger,
                device_name=pump_info["DeviceName"],
                Nextpump_Addr=pump_info["ADDRESS"],
                solution_name=solvent_type,
                PORT=pump_info["PORT"],
                baudrate=pump_info["BAUDRATE"],
                set_direction=pump_info["set_direction"],
            )
        return pumps

    # --------------------------
    # Liquid transfer step
    # --------------------------
    def transfer_liquid(self):
        self.logger.info("Starting liquid transfer sequence")
        for batch_num in range(self.batch_size):
            pickandplaceXYZActuator(
                self.logger,
                pick_num=batch_num,
                action_type="holder_to_XYZ_vial",
                mode_type=self.mode_type,
            )
        self.tcp_obj.callServer_INK(
            f"PRE_XYZ_Actuator/TransferLiquid/{self.batch_size}/3/real"
        )

    # --------------------------
    # Solution addition step
    # --------------------------
    def add_solution(self):
        self.logger.info("Starting solution addition step")
        if len(self.solvents) != len(self.volumes):
            self.logger.error("Mismatch between number of solvents and volumes.")
            return

        for batch_num in range(self.batch_size):
            self.logger.info(f"Processing batch {batch_num + 1}/{self.batch_size}")
            pickandplaceDeskLA(
                self.logger,
                pick_num=batch_num,
                action_type="holder_to_DeskLA",
                mode_type=self.mode_type,
            )
            self.deskla_obj.DeskLA_To_Washing(mode_type=self.mode_type)
            self.dispenser_obj.DispenserLA_Action(
                action_type="AddSolution", mode_type=self.mode_type
            )
            time.sleep(1)

            for solvent, volume_ml in zip(self.solvents, self.volumes):
                if solvent in ["Acetone", "Ethanol", "H2O"]:
                    xcal_obj = XCaliburD(self.logger, device_name=solvent)
                    self.logger.info(
                        f"[ADD] Using XCaliburD for {solvent}, {volume_ml} mL"
                    )

                    self.dispenser_obj.DispenserServo(
                        action_type=solvent, mode_type=self.mode_type
                    )
                    desired_ul = volume_ml * 1000
                    max_ul = 5000
                    cycles = desired_ul // max_ul
                    leftover = desired_ul % max_ul

                    for _ in range(int(cycles)):
                        xcal_obj.add(
                            volume=max_ul, flow_rate=40000, mode_type=self.mode_type
                        )
                    if leftover > 0:
                        xcal_obj.add(
                            volume=leftover, flow_rate=40000, mode_type=self.mode_type
                        )

            self.dispenser_obj.DispenserServo_Remove(mode_type=self.mode_type)
            self.dispenser_obj.DispenserLA_Action(
                action_type="HOME_AddSolution", mode_type=self.mode_type
            )
            self.deskla_obj.DeskLA_To_HOME(mode_type=self.mode_type)
            pickandplaceDeskLA(
                self.logger,
                pick_num=batch_num,
                action_type="DeskLA_to_holder",
                mode_type=self.mode_type,
            )

    # --------------------------
    # Centrifugation step
    # --------------------------
    def centrifugation(self):
        self.logger.info("Starting centrifugation step")
        for batch_num in range(self.batch_size):
            CentriTaskwithVision(
                self.logger,
                batch_num,
                action_type="place_falcon_to_centri",
                mode_type=self.mode_type,
            )

        self.centri_obj.LA_CLOSE(mode_type=self.mode_type)
        self.Centrimanager.CentriStart(
            set_time=self.centri_time, mode_type=self.mode_type
        )
        self.Centrimanager.button_stop()
        self.Centrimanager.close_all_ports()
        self.centri_obj.LA_OPEN(mode_type=self.mode_type)

        changetheGripper(
            self.logger,
            action_type="change_the_gripper_to_VCG",
            mode_type=self.mode_type,
        )
        for batch_num in range(self.batch_size):
            CentriTaskwithVision(
                self.logger,
                batch_num,
                action_type="pick_falcon_from_centri",
                mode_type=self.mode_type,
            )
        changetheGripper(
            self.logger,
            action_type="change_the_gripper_to_RG6",
            mode_type=self.mode_type,
        )

    def sonicTask(self):
        for batch_num in range(self.batch_size):
            pickandplaceSonic(
                self.logger,
                pick_num=batch_num,
                action_type="holder_to_sonic",
                mode_type=self.mode_type,
            )
        self.sonic_obj.operate(
            set_time=self.sonic_set_time, target_temp=0, mode_type=self.mode_type
        )
        for batch_num in range(self.batch_size):
            pickandplaceSonic(
                self.logger,
                pick_num=batch_num,
                action_type="sonic_to_holder",
                mode_type=self.mode_type,
            )

    def handle_failure_with_LLM(self, logger, failed_recipe, fail_reason_text):
        """
        When centrifugation fails, request a new recipe from LLM.
        The decision to use RAG is explicitly controlled by user or recipe metadata.
        """
        retriever = WashingMethodRetrival()
        recipe_generator = RecipeGenerator(retriever)

        # Get user-defined RAG flag (default: True)
        use_rag = failed_recipe["metadata"].get("use_rag", True)

        logger.info(
            f"Centrifugation failure detected. Invoking LLM (use_rag={use_rag})"
        )

        new_recipe = recipe_generator.generate_recipe(
            synthesis_description="Centrifugation failure occurred. Adjust parameters for next attempt.",
            synthesized_reagents=list(
                failed_recipe["metadata"].get("Reagent_Information", {}).keys()
            ),
            previous_recipe=failed_recipe,
            fail_reason_text=fail_reason_text,
            use_rag=use_rag,
        )

        # Save new recipe
        from datetime import datetime
        import json, os

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"./results/generated_recipe_{timestamp}.json"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(new_recipe, f, indent=4, ensure_ascii=False)

        logger.info(f"New recipe generated and saved to: {save_path}")
        return new_recipe

    def remove_liquid(self):
        """
        Perform liquid removal per batch.
        If a specific batch fails, call handle_failure_with_LLM() to generate a new recipe
        for remaining or failed batches only.
        """

        self.logger.info(
            "Starting vision verification for each batch before liquid removal..."
        )
        failed_batches = []

        for batch_num in range(self.batch_size):
            # Move holder to DeskLA position
            pickandplaceDeskLA(
                self.logger,
                batch_num,
                action_type="holder_to_DeskLA",
                mode_type=self.mode_type,
            )

            # Run vision detection
            vision_result = ViewPointAlgorithm(self.logger, mode_type=self.mode_type)

            if vision_result == "success":
                self.logger.info(
                    f"✅ Batch {batch_num + 1}: Centrifugation success → Removing liquid."
                )
                self.dispenser_obj.DispenserLA_Action(
                    action_type="RemoveLiquid", mode_type=self.mode_type
                )
                self.remove_liquid_pump.Filling(
                    target_time=40, target_volume=60, mode_type=self.mode_type
                )
                self.dispenser_obj.DispenserLA_Action(
                    action_type="HOME_RemoveLiquid", mode_type=self.mode_type
                )
                self.deskla_obj.DeskLA_To_HOME(mode_type=self.mode_type)
                pickandplaceDeskLA(
                    self.logger,
                    batch_num,
                    action_type="DeskLA_to_holder",
                    mode_type=self.mode_type,
                )
            else:
                self.logger.warning(f"⚠️ Batch {batch_num + 1}: Centrifugation failed.")
                failed_batches.append(batch_num + 1)
                self.deskla_obj.DeskLA_To_HOME(mode_type=self.mode_type)
                pickandplaceDeskLA(
                    self.logger,
                    batch_num,
                    action_type="DeskLA_to_holder",
                    mode_type=self.mode_type,
                )

        # ----------------------------- #
        # Step 2: If any batch failed → call LLM
        # ----------------------------- #
        if failed_batches:
            fail_reason = f"Centrifugation failed in batches {failed_batches}. Adjust only those parameters."
            self.logger.warning(
                f"❗ Partial failure detected — batches {failed_batches}."
            )
            new_recipe = self.handle_failure_with_LLM(
                self.logger, self.recipe, fail_reason
            )
            return {
                "status": "partial_failure",
                "failed_batches": failed_batches,
                "new_recipe": new_recipe,
            }

        self.logger.info("✅ All batches completed successfully.")
        return {"status": "success"}


if __name__ == "__main__":
    """
    Main execution entry point.
    Runs the full washing sequence including vision-based centrifugation evaluation
    and LLM feedback loop in case of failure.
    """
    # ----------------------------- #
    # Step 1: Logger initialization
    # ----------------------------- #
    logger = NodeLogger(
        platform_name="Washing Task",
        setLevel="DEBUG",
        SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log",
    )

    logger.info("=== Starting Automated Washing Workflow ===")

    # ----------------------------- #
    # Step 2: Load or define initial recipe
    # ----------------------------- #
    initial_recipe = {
        "metadata": {
            "subject": "CentrifugationTask",
            "group": "KIST_CSRC",
            "logLevel": "DEBUG",
            "BatchSize": 6,
            "TransferLiquid": 3,
            "NumberofCentrifugation": 3,
            "Reagent_Information": {
                "Ruthenium(III) chloride hydrate": {
                    "volume_mL": 2,
                    "concentration_mol": 0.0265,
                },
                "Iridium(III) chloride hydrate": {
                    "volume_mL": 2,
                    "concentration_mol": 0.0135,
                },
                "Hexadecyltrimethylammonium bromide": {
                    "volume_mL": 0.03,
                    "concentration_mol": 1,
                },
                "Sodium borohydride": {"volume_mL": 3, "concentration_mol": 0.3},
            },
            "PriorityReferenceColor": "Blue",
            "Constraints_Reagents_Volume": 40,
            "InstalledSolvent": ["H2O", "Ethanol", "Acetone"],
            "VisionModel": "",
            "mode_type": "real",
        },
        "process": {
            "Sequence": [
                "TransferLiquid",
                "AddSolution",
                "Centrifugation",
                "RemoveLiquid",
            ],
            "Solvents": ["Ethanol", "H2O"],
            "Solvents_Volume": [20, 20],
            "CentrifugationRPM": 8000,
            "CentrifugationTime": 1200,
        },
        "ReasonofAnswer": {},
        "FailHistory": [],
    }

    # ----------------------------- #
    # Step 3: Initialize washing task
    # ----------------------------- #
    washing_task = WashingTask(logger, initial_recipe)
    try:
        # ----------------------------- #
        # Step 4: Washing sequence execution
        # ----------------------------- #
        logger.info("Running full washing sequence...")
        washing_task.transfer_liquid()
        washing_task.add_solution()
        washing_task.centrifugation()
        result = washing_task.remove_liquid()

        # ----------------------------- #
        # Step 5: If centrifugation failed, invoke LLM
        # ----------------------------- #
        if isinstance(result, dict):
            if result.get("status") == "partial_failure":
                new_recipe = result["new_recipe"]
            else:
                logger.info("✅ Washing completed successfully.")
                exit(0)
        elif result == "failure":
            new_recipe = washing_task.handle_failure_with_LLM(
                washing_task.recipe,
                fail_reason_text="No precipitate detected during centrifugation.",
            )
        else:
            logger.info("✅ Washing process completed successfully.")
            exit(0)
            # ----------------------------- #
        # Step 6: Re-run with new recipe
        # ----------------------------- #
        logger.info("Re-initializing washing task with new recipe from LLM...")
        washing_task = WashingTask(logger, new_recipe)
        washing_task.transfer_liquid()
        washing_task.add_solution()
        washing_task.centrifugation()
        washing_task.remove_liquid()

        logger.info("=== Adaptive Washing Workflow Completed ===")

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
