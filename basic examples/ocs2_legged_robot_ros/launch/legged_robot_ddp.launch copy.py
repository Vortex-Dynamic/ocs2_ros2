import os
import shutil
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def is_wsl():
    """Detect if running under Windows Subsystem for Linux."""
    try:
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            return 'microsoft' in version_info or 'wsl' in version_info
    except FileNotFoundError:
        return False


def generate_launch_description():
    # -------------------------------
    # Detect terminal type
    # -------------------------------
    if shutil.which("tmux"):
        prefix = "tmux new-window -d -n rosnode"
        print("Using tmux for terminals")
    elif shutil.which("terminator") and os.getenv("DISPLAY"):
        prefix = "terminator --new-tab -x"
        print("Terminator is installed and X available, using terminator")
    elif is_wsl():
        prefix = "xterm -e"
        print("Detected WSL environment, using xterm")
    elif shutil.which("gnome-terminal") and os.getenv("DISPLAY"):
        prefix = "gnome-terminal --"
        print("Using gnome-terminal")
    else:
        prefix = ""
        print("No GUI terminal found; running inline")

    # -------------------------------
    # Resolve file paths
    # -------------------------------
    task_file = os.path.join(
        get_package_share_directory('ocs2_legged_robot'), 'config/mpc/task.info')
    reference_file = os.path.join(
        get_package_share_directory('ocs2_legged_robot'), 'config/command/reference.info')
    urdf_file = os.path.join(
        get_package_share_directory('ocs2_robotic_assets'), 'resources/anymal_c/urdf/anymal.urdf')
    gait_command_file = os.path.join(
        get_package_share_directory('ocs2_legged_robot'), 'config/command/gait.info')

    # -------------------------------
    # Launch Arguments
    # -------------------------------
    description_name = LaunchConfiguration('description_name')
    multiplot = LaunchConfiguration('multiplot')
    taskFile = LaunchConfiguration('taskFile')
    referenceFile = LaunchConfiguration('referenceFile')
    urdfFile = LaunchConfiguration('urdfFile')
    gaitCommandFile = LaunchConfiguration('gaitCommandFile')
    foxglove = LaunchConfiguration('foxglove')

    # -------------------------------
    # Launch Description
    # -------------------------------
    return LaunchDescription([
        SetEnvironmentVariable('LAUNCH_PREFIX', prefix),

        # User-selectable options
        DeclareLaunchArgument('description_name', default_value='legged_robot_description'),
        DeclareLaunchArgument('multiplot', default_value='false'),
        DeclareLaunchArgument('foxglove', default_value='true'),

        DeclareLaunchArgument('taskFile', default_value=task_file),
        DeclareLaunchArgument('referenceFile', default_value=reference_file),
        DeclareLaunchArgument('urdfFile', default_value=urdf_file),
        DeclareLaunchArgument('gaitCommandFile', default_value=gait_command_file),

        # -------------------------------
        # Core Included Launches
        # -------------------------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/basic.launch.py']),
            launch_arguments={
                'rviz': 'false',  # disable RViz
                'description_name': description_name,
                'multiplot': multiplot,
            }.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/mpc_ddp.launch.py']),
            launch_arguments={
                'referenceFile': referenceFile,
                'taskFile': taskFile,
                'urdfFile': urdfFile,
            }.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/dummy.launch.py']),
            launch_arguments={
                'referenceFile': referenceFile,
                'taskFile': taskFile,
                'urdfFile': urdfFile,
            }.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/gait_command.launch.py']),
            launch_arguments={
                'gaitCommandFile': gaitCommandFile,
            }.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/robot_target.launch.py']),
            launch_arguments={
                'referenceFile': referenceFile,
            }.items(),
        ),

        # -------------------------------
        # FOXGLOVE BRIDGE (conditional)
        # -------------------------------
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{
                'port': 8765,           # Default Foxglove WebSocket port
                'address': '0.0.0.0',   # Allow external connections
                'send_buffer_limit': 10000000
            }],
            condition=IfCondition(foxglove)
        ),
    ])