"""Regression tests for testing simulation setup"""

import shutil
import os
import filecmp

from regression import RegressionTest


class TestSetupWithRestraints(RegressionTest):

    def setup(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.test_path = self.path + '/scratch_setup_restraints/'
        self.ini_test_path()
        self.golden_data_path = os.path.normpath(os.path.dirname(os.path.realpath(__file__))) + \
                                '/golden_data/regression_setup_rst/'
        shutil.copy(os.path.join(self.golden_data_path, '2UUY_rec.pdb'), self.test_path)
        shutil.copy(os.path.join(self.golden_data_path, '2UUY_lig.pdb'), self.test_path)
        shutil.copy(os.path.join(self.golden_data_path, 'restraints.list'), self.test_path)

    def teardown(self):
        self.clean_test_path()

    def test_lightdock_setup_with_restraints(self):
        os.chdir(self.test_path)
        num_swarms = 10
        num_glowworms = 10

        command = "lightdock_setup %s %s %d %d --noxt -anm -rst %s > test_lightdock.out" % ('2UUY_rec.pdb',
                                                                                            '2UUY_lig.pdb',
                                                                                            num_swarms,
                                                                                            num_glowworms,
                                                                                            'restraints.list'
                                                                                            )
        os.system(command)

        assert filecmp.cmp(self.golden_data_path + 'init/initial_positions_0.dat',
                           self.test_path + 'init/initial_positions_0.dat')
        assert filecmp.cmp(self.golden_data_path + 'init/initial_positions_1.dat',
                           self.test_path + 'init/initial_positions_1.dat')
        assert filecmp.cmp(self.golden_data_path + 'setup.json',
                           self.test_path + 'setup.json')
