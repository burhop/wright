# CSV upload / ROS 2 bag preparation
This file is original synthetic input documentation, not a bag or a successful-conversion record.
| Input | Topic | Intended ROS 2 message | Mapping |
|---|---|---|---|
| planned-path.csv | /wright_test/planned_pose | geometry_msgs/msg/PoseStamped | time_s to header.stamp; frame_id to header.frame_id; x_m/y_m/z_m=0; quaternion from yaw_rad |
| external-pose.csv | /wright_test/external_pose | geometry_msgs/msg/PoseStamped | timestamp_s to header.stamp; frame_id unchanged; omit rows whose valid field is 0; quaternion from yaw_rad |
| odometry.csv | /wright_test/odom | nav_msgs/msg/Odometry | time_s to header.stamp; frame_id and child_frame_id preserved; pose x/y/yaw; twist linear.x and angular.z |
| velocity-command.csv | /wright_test/cmd_vel | geometry_msgs/msg/TwistStamped | time_s to header.stamp; frame_id=base_link; linear.x=linear_mps; angular.z=angular_radps |
| events.csv | /wright_test/operator_event | std_msgs/msg/String | record event at the time_s bag timestamp, preserve full text |
Use a fixed synthetic epoch of 2026-01-01T00:00:00Z for all elapsed timestamps. Preserve a conversion manifest with source hashes, epoch, serialization version and topic schemas. Header offsets intentionally provided in context.md must not be removed during conversion. A missing external pose is absence of a message, not a zero coordinate. Covariance is unknown; do not fabricate measured confidence. Bag recording timestamp for external-pose rows is time_s (acquisition-clock timeline); header time is timestamp_s. These differ in the clock-offset scenario.
The person running the scenario can upload these CSVs and this mapping; bag conversion is environment preparation, not manual input fabrication.
