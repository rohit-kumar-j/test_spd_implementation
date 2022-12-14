import mujoco
import numpy as np


def get_all_joint_indices(model, jnt_name):
    jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jnt_name)
    print(f"model.njnt: {model.njnt}")
    print(f"model.nv: {model.nv}")
    print(f"jnt_id: {jnt_id}")
    print(f"model.jnt_dofadr: {model.jnt_dofadr}")
    adr_start = model.jnt_dofadr[jnt_id]
    vel_adr_start = model.jnt_qposadr[jnt_id]
    print(f"adr_start: {adr_start}")

    print(f"model.jnt_type: {model.jnt_type}")

    # assuming only ball, hinge or slide is used
    # Types of free, ball, slide, hinge: 0, 1, 2, 3
    if model.jnt_type[jnt_id] == 0:
        n_dofs = 6
        print("free")
    elif model.jnt_type[jnt_id] == 1:
        n_dofs = 3
        print("ball")
    elif model.jnt_type[jnt_id] == 2:
        n_dofs = 1
        print("slide")
    elif model.jnt_type[jnt_id] == 3:
        n_dofs = 1
        print("hinge")
    # n_dofs = 1 if model.jnt_type[jnt_id] > 1 else 3
    return np.arange(adr_start, adr_start + n_dofs)


def computePD(
    model,
    data,
    controlled_joint_ids,
    desiredPositions,
    desiredVelocities,
    kps,
    kds,
    maxForces,
    timeStep,
):
    qposadr = model.jnt_qposadr[
        model.body_jntadr[
            mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, "my_floating_body"
            )
        ]
    ]

    q = np.array(
        [
            data.qpos[0],
            data.qpos[1],
            data.qpos[2],
        ]
    )
    qdot = np.array(
        [
            data.qvel[0],
            data.qvel[1],
            data.qvel[2],
        ]
    )
    q_des = np.array(desiredPositions)
    qdot_des = np.array(desiredVelocities)

    Kp = np.diagflat(kps)
    Kd = np.diagflat(kds)

    # Create empty mass matrix
    MassMatrix = np.empty(
        shape=(model.nv, model.nv),
        dtype=np.float64,
    )

    # Creates in self._data.crb
    mujoco.mj_crb(model, data)

    mujoco.mj_fullM(
        model,
        MassMatrix,
        data.qM,
    )

    Bias_Forces = data.qfrc_bias

    print(f"q: {q},np.shape(q):{np.shape(q)}")
    print(f"q_des: {q_des},np.shape(q_des):{np.shape(q_des)}")
    print(f"qdot: {qdot},np.shape(qdot):{np.shape(qdot)}")
    print(f"qdot_des: {qdot_des},np.shape(qdot_des):{np.shape(qdot_des)}")
    # print(f"Kp: {Kp},np.shape(Kp):{np.shape(Kp)}")
    print(f"Kd: {Kd},np.shape(Kd):{np.shape(Kd)}")
    print(
        f"MassMatrix: {MassMatrix[:3,:3]},np.shape(MassMatrix):{np.shape(MassMatrix[:3,:3])}"
    )
    print(
        f"Bias_Forces: {Bias_Forces[:3]},np.shape(Bias_Forces):{np.shape(Bias_Forces[:3])}"
    )
    dof_indices = np.concatenate(
        [
            get_all_joint_indices(model, joint_id)
            for joint_id in controlled_joint_ids
        ]
    )

    qError = q_des - q
    qdotError = qdot_des - qdot

    # Compute -Kp(q + qdot - qdes)
    # p_term = Kp.dot(qError - qdot * timeStep)

    # Compute -Kd(qdot - qdotdes)
    # d_term = Kd.dot(qdotError)
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
    print(f"MM: {MassMatrix[dof_indices, dof_indices]}")
    print(f"dof_indices: {dof_indices}")

    qddot = np.linalg.solve(
        a=(MassMatrix[:dof_indices, :dof_indices] + Kd * timeStep),
        b=(
            -Bias_Forces[dof_indices]
            + Kp.dot(qError - qdot * timeStep)
            + Kd.dot(qdotError)
        ),
    )

    tau = (
        Kp.dot(qError - qdot * timeStep)
        + Kd.dot(qdotError)
        - (Kd.dot(qddot) * timeStep)
    )

    # Clip generalized forces to actuator limits
    maxF = np.array(maxForces)
    generalized_forces = np.clip(tau, -maxF, maxF)
    return generalized_forces


def show_actuator_forces(
    viewer,
    data,
    rendered_axes,
    f_render,
    f_list,
    show_force_labels=False,
) -> None:
    if show_force_labels is False:
        label = ""
        for i in rendered_axes:
            viewer.add_marker(
                pos=data.site(f_render[i][1]).xpos,
                mat=data.site(f_render[i][1]).xmat,
                size=[
                    0.02,
                    0.02,
                    (data.actuator_force[f_list[i]] / f_render[i][2]),
                ],
                rgba=f_render[i][3],
                type=mujoco.mjtGeom.mjGEOM_ARROW,
                label=label,
            )
    else:
        for i in rendered_axes:
            viewer.add_marker(
                pos=data.site(f_render[i][1]).xpos,
                mat=data.site(f_render[i][1]).xmat,
                size=[
                    0.02,
                    0.02,
                    (data.actuator_force[f_list[i]] / f_render[i][2]),
                ],
                rgba=f_render[i][3],
                type=mujoco.mjtGeom.mjGEOM_ARROW,
                label=str(data.actuator_force[f_list[i]]),
            )


def populate_show_actuator_forces(model, to_be_rendered_axes) -> None:
    """
    format :
        self._f_render = {
            "axis_name": ["act_name","geom_for_force_render","scaling"]
        }

        self._f_list = {
            "axis_name": ["actuator_index"], # internally generated
        }
    """
    rendered_axes = to_be_rendered_axes

    f_render = {
        "hinge_1": [
            "pos_servo_1",
            "site_1",
            20.0,
            [1, 0, 1, 0.2],
        ],
        "hinge_2": [
            "pos_servo_2",
            "site_2",
            20.0,
            [1, 0, 1, 0.2],
        ],
        "hinge_3": [
            "pos_servo_3",
            "site_3",
            20.0,
            [1, 0, 1, 0.2],
        ],
    }
    f_list_keys = []
    f_list_values = []
    for key in rendered_axes:
        values = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_ACTUATOR,
            f_render[key][0],
        )
        # print("values:", values)
        f_list_keys.append(key)
        f_list_values.append(values)
    f_list = dict(zip(f_list_keys, f_list_values))
    # print("self._f_list:", f_list)

    return rendered_axes, f_render, f_list
