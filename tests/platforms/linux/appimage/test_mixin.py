import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import (
    LinuxAppImageBuildCommand,
    LinuxAppImageCreateCommand,
)


@pytest.fixture
def create_command(tmp_path):
    return LinuxAppImageCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_project_path(create_command, first_app_config, tmp_path):
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"
    project_path = create_command.project_path(first_app_config)

    assert project_path == tmp_path / "base_path" / "linux" / "appimage" / "First App"


def test_binary_path(create_command, first_app_config, tmp_path):
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"
    binary_path = create_command.binary_path(first_app_config)

    assert (
        binary_path
        == tmp_path / "base_path" / "linux" / "First_App-0.0.1-x86_64.AppImage"
    )


def test_distribution_path(create_command, first_app_config, tmp_path):
    # Force the architecture to x86_64 for test purposes.
    create_command.tools.host_arch = "x86_64"
    distribution_path = create_command.distribution_path(first_app_config, "appimage")

    assert (
        distribution_path
        == tmp_path / "base_path" / "linux" / "First_App-0.0.1-x86_64.AppImage"
    )


def test_docker_image_tag(create_command, first_app_config, tmp_path):
    image_tag = create_command.docker_image_tag(first_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_docker_image_tag_uppercase_name(
    create_command, uppercase_app_config, tmp_path
):
    image_tag = create_command.docker_image_tag(uppercase_app_config)

    assert image_tag == f"briefcase/com.example.first-app:py3.{sys.version_info.minor}"


def test_verify_linux_no_docker(create_command, tmp_path, first_app_config):
    """If Docker is disabled on Linux, the app_context is Subprocess."""
    create_command.tools.host_os = "Linux"
    create_command.use_docker = False

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # No error and Subprocess is used.
    assert isinstance(create_command.tools[first_app_config].app_context, Subprocess)
    # Docker is not verified.
    assert not hasattr(create_command.tools, "docker")


def test_verify_linux_docker(create_command, tmp_path, first_app_config, monkeypatch):
    """If Docker is enabled on Linux, the Docker alias is set."""
    create_command.tools.host_os = "Linux"
    create_command.use_docker = True

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=create_command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )


def test_verify_non_linux_docker(create_command, tmp_path, first_app_config):
    """If Docker is enabled on non-Linux, the Docker alias is set."""
    create_command.tools.host_os = "Darwin"
    create_command.use_docker = True

    # Mock Docker tool verification
    Docker.verify = MagicMock()
    DockerAppContext.verify = MagicMock()

    # Verify the tools
    create_command.verify_tools()
    create_command.verify_app_tools(app=first_app_config)

    # Docker and Docker app context are verified
    Docker.verify.assert_called_with(tools=create_command.tools)
    DockerAppContext.verify.assert_called_with(
        tools=create_command.tools,
        app=first_app_config,
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )


def test_clone_options(tmp_path):
    """Docker options are cloned."""
    build_command = LinuxAppImageBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    build_command.use_docker = True

    create_command = build_command.create_command

    # Confirm the use_docker option has been cloned.
    assert create_command.is_clone
    assert create_command.use_docker
