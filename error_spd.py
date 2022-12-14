import math
import mujoco
import numpy as np
from mujoco_viewer import MujocoViewer
from error_spd_utils import (
    computePD,
    populate_show_actuator_forces,
    show_actuator_forces,
    get_all_joint_indices,
)

model = mujoco.MjModel.from_xml_path("pendulum_simple_position.xml")
data = mujoco.MjData(model)
viewer = MujocoViewer(model, data)

# viewer.add_graph_line(line_name="sine_wave", line_data=0.0)
# viewer.add_graph_line(line_name="position_sensor", line_data=0.0)
viewer.add_graph_line(line_name="force", line_data=0.0)
viewer.add_graph_line(line_name="joint_pos_error", line_data=0.0)
x_div = 10
y_div = 10
viewer.set_grid_divisions(x_div=x_div, y_div=y_div, x_axis_time=0.5)
viewer.show_graph_legend()

viewer.callbacks._paused = True
t = 0

general_kp = 10000 * 2
general_kd = general_kp * model.opt.timestep * 1.9

rendered_axes, f_render, f_list = populate_show_actuator_forces(
    model=model,
    to_be_rendered_axes=[
        "hinge_1",
        "hinge_2",
        "hinge_3",
    ],
)

h1 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "hinge_1")
h2 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "hinge_2")
h3 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "hinge_3")


while True:
    target_pos = math.sin(t * 0.0001 * (180 / math.pi))
    next_pos = math.sin((t + 1) * 0.0001 * (180 / math.pi))
    target_vel = next_pos - target_pos / model.opt.timestep
    error = target_pos - data.qpos[0].tolist()

    qposadr = model.jnt_qposadr[
        model.body_jntadr[
            mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, "my_floating_body"
            )
        ]
    ]
    qveladr = model.jnt_dofadr[
        model.body_jntadr[
            mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, "my_floating_body"
            )
        ]
    ]
    print(f"qposadr: {qposadr}")
    print(f"qveladr: {qveladr}\n")
    print("\n\n", get_all_joint_indices(model, "hinge_1"), "\n\n")
    print("\n\n", get_all_joint_indices(model, "hinge_2"), "\n\n")
    print("\n\n", get_all_joint_indices(model, "hinge_3"), "\n\n")

    print("\n\n", get_all_joint_indices(model, "box_free_j"), "\n\n")
    # dof_indices = np.concatenate(
    #     [
    #         get_all_joint_indices(model, joint_id)
    #         for joint in controlled_joint_ids
    #     ]
    # )

    # sub_M = full_M[dof_indices, dof_indices]
    # sub_bias = bias[dof_indices]

    spd_forces = computePD(
        model=model,
        data=data,
        controlled_joint_ids=["hinge1", "hinge2", "hinge3"],
        desiredPositions=[target_pos, -target_pos, target_pos],
        desiredVelocities=[0] * model.nu,
        kps=[general_kp] * model.nu,
        kds=[general_kd] * model.nu,
        maxForces=[1000] * model.nu,
        timeStep=model.opt.timestep,
        # body_name="link_1",  # ,"my_floating_body",
    )

    show_actuator_forces(
        viewer=viewer,
        data=data,
        rendered_axes=rendered_axes,
        f_render=f_render,
        f_list=f_list,
        show_force_labels=True,
    )

    t = t + 1
    print("data.ctrl: ", data.ctrl, "spd_forces:", spd_forces)
    data.ctrl = spd_forces

    mujoco.mj_step(model, data)
    viewer.render()

    # viewer.update_graph_line(
    #     line_name="sine_wave",
    #     line_data=target_pos,
    # )
    # viewer.update_graph_line(
    #     line_name="position_sensor",
    #     line_data=data.qpos[0],
    # )
    viewer.update_graph_line(
        line_name="force",
        line_data=spd_forces[0],
    )
    viewer.update_graph_line(
        line_name="joint_pos_error",
        line_data=error,
    )
