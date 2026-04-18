from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import BRCMBuildingSimulator
from alphabuilding.control.utils import load_learned_lti_ss

plant = BRCMBuildingSimulator.from_mat_file(global_config.BRCM_MAT_FILE)


sys_learned, dm, L_learned, cfg = load_learned_lti_ss(auto_select_last=True)
