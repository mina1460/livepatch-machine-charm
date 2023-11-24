# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests configuration helpers and fixtures."""
import logging
from pathlib import Path

import pytest
from integration.utils import fetch_charm
from pytest_operator.plugin import OpsTest

LOGGER = logging.getLogger(__name__)

# Fixtures to handle the deployment per each test suite.
# ops_test is a module fixture, which kind of limits us in what we
# can do regarding building artifacts required for the tests.
# As such, we run a subproc validating the snap version
# such that we don't have to try build it over and over.
#
# As for the charm, we should probably do the same. But for
# now we use the built in ops_test.build_charm


@pytest.fixture(name="charm_path", scope="module")
async def build_charm_fixture(ops_test: OpsTest):
    """A fixture to Build the charm."""
    LOGGER.info("Building charm.")
    charm_path = await fetch_charm(ops_test)
    yield charm_path


@pytest.fixture(name="bundle_path", scope="module")  # charm_path: str)
def render_bundle_fixture(ops_test: OpsTest, charm_path: str):
    """Render bundle fixture."""
    LOGGER.info("Rendering bundle with snap and charm paths.")
    charm_directory = Path.cwd()
    tests_directory = charm_directory.joinpath("tests")
    tests_data_directory = tests_directory.joinpath("data")
    bundle_path = tests_data_directory.joinpath("int-test-bundle.yaml")

    rendered_bundle_path = ops_test.render_bundle(
        bundle_path,
        charm_path=charm_path,
    )
    LOGGER.info("Bundle path is: %s", str(rendered_bundle_path.absolute()))
    yield rendered_bundle_path


# TODO: Move this into setupTest funcs and turns the bundlepath & snap/charm build fixture
# into session fixtures. Then pull bundle path into each setupTest lifecycle func and
# deploy per each test suite.
@pytest.fixture(name="deploy_built_bundle", scope="module")
async def deploy_bundle_function(ops_test: OpsTest, bundle_path: Path):
    """Deploy bundle function."""
    juju_cmd = [
        "deploy",
        "-m",
        ops_test.model_full_name,
        str(bundle_path.absolute()),
    ]
    rc, stdout, stderr = await ops_test.juju(*juju_cmd)
    if rc != 0:
        raise FailedToDeployBundleError(stderr, stdout)


class FailedToDeployBundleError(Exception):
    """Exception raised when bundle fails to deploy.

    Attributes:
        stderr -- todo
        stdout -- todo
    """

    def __init__(self, stderr, stdout):
        self.message = f"Bundle deploy failed: {(stderr or stdout).strip()}"
        super().__init__(self.message)
