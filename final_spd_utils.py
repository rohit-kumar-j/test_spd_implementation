import pprint
import mujoco
import numpy as np


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

    # get pos and vel
    q = []
    qdot = []
    for i in controlled_joint_ids:
        q.append(data.joint(i).qpos[0])
        qdot.append(data.joint(i).qvel[0])

    q = np.array(q)
    qdot = np.array(qdot)

    # print(f"q: {q}")
    # print(f"qdot: {qdot}")

    dof_indices = []
    for i in controlled_joint_ids:
        jnt_id = model.joint(i).dofadr[0]
        # adr_start = model.jnt_dofadr[jnt_id]
        # adr_start = model.jnt_dofadr[jnt_id]

        # if model.jnt_type[jnt_id] == 0:
        #     n_dofs = 6
        #     print("free")
        # elif model.jnt_type[jnt_id] == 1:
        #     n_dofs = 3
        #     print("ball")
        if model.joint(i).type == 2:
            n_dofs = 1
            # print("slide")
        elif model.joint(i).type == 3:
            n_dofs = 1
            # print("hinge")

        x = np.arange(model.joint(i).dofadr, model.joint(i).dofadr + n_dofs)
        # dof_indices.append(model.joint(i).dofadr[0])
        dof_indices.append(x[0])

    # print(f"dof_indices: {dof_indices}")

    ##########################################################################

    q_des = np.array(desiredPositions)
    qdot_des = np.array(desiredVelocities)

    # print(f"q_des: {q_des}")
    # print(f"qdot_des: {qdot_des}")

    Kp = np.diagflat(kps)
    Kd = np.diagflat(kds)
    # print(f"Kp: {Kp}")
    # print(f"Kd: {Kd}")

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

    MassMatrix = MassMatrix[dof_indices, :][:, dof_indices]

    Bias_Forces = data.qfrc_bias[dof_indices]

    # print(f"MassMatrix: {MassMatrix}")
    # print(f"Bias_Forces: {Bias_Forces}")

    qError = q_des - q
    qdotError = qdot_des - qdot

    # Compute -Kp(q + qdot - qdes)
    p_term = Kp.dot(qError - qdot * timeStep)

    # Compute -Kd(qdot - qdotdes)
    d_term = Kd.dot(qdotError)

    qddot = np.linalg.solve(
        a=(MassMatrix + Kd * timeStep),
        b=(-Bias_Forces + p_term + d_term),
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
        "hinge_2_1": [
            "pos_servo_2_1",
            "site_2_1",
            20.0,
            [1, 0, 1, 0.2],
        ],
        "hinge_3_1": [
            "pos_servo_3_1",
            "site_3_1",
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
