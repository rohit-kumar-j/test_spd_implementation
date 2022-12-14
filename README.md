# Test-SPD-Implementation

Test SPD implementation for mujoco from
**Stable proportional-derivative controllers**
DOI: 10.1109/MCG.2011.30

Fixed based robot SPD in `simple_spd.py`

Simple P controller with joint damping in `simple_position.py`

Shape error at higher DOFs `error_spd.py`

Works with extra free bodies added to the sim: `static_implementation.py` [stable at timestep = 0.1s]

**Current**: Let robot have free link - `final_implementation_spd.py`
is spd a good strategy?: depends on the kp and kd tuning

**TODO**: Reduce variable creation
**TODO**: ball joints (also free joints?)
___________________

| SPD Low timestep(0.005s) | SPD High timestep(0.05s) |
|:----------------:|:-----------------:|
| <video src="https://user-images.githubusercontent.com/37873142/187661027-01c710dd-becc-446c-b885-459b9a6ea923.mp4"> |  <video src="https://user-images.githubusercontent.com/37873142/187661081-fe6be6a6-397a-4255-9edb-815b42108aa6.mp4"> |

| Simple P Low timestep(0.005s) | Simple P High timestep(0.05s) |
|:---------------------:|:----------------------:|
| <video src="https://user-images.githubusercontent.com/37873142/187661333-57c707cf-e7cd-4678-a2ae-e36ef6f94870.mp4"> | <video src="https://user-images.githubusercontent.com/37873142/187661414-f42be449-163a-4a66-8c5d-b8ffe2518258.mp4"> |
___________________
## External
uses pybullet for easy gui based sliders
