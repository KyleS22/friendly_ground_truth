"""
File Name: test_controller.py

Authors: Kyle Seidenthal

Date: 09-03-2020

Description: Test cases for the controller moduel

"""

import pytest
import os
import wx
import mock

from friendly_ground_truth.controller.controller import Controller
from friendly_ground_truth.view.view import MainWindow


class TestController:
    """
    Tests pertaining to the controller class
    """

    @pytest.fixture
    def valid_rgb_image_path(self):
        return os.path.abspath('tests/data/KyleS22.jpg')

    @pytest.fixture
    def valid_grayscale_image_path(self):
        return os.path.abspath('tests/data/KyleS22_gray.png')

    @pytest.fixture
    def invalid_image_path(self):
        return 'invalid/image/path'

    @pytest.fixture
    def directory_path(self):
        return os.path.abspath('tests/data/')

    @pytest.fixture
    def setup(self, mocker):

        self.mock_MW_init = mocker.patch.object(MainWindow, '__init__', lambda x, y: None)
        self.mock_MW_Show = mocker.patch.object(MainWindow, 'Show')
        self.mock_C_display_current_patch = mocker.\
                                            patch.\
                                            object(Controller,
                                                   'display_current_patch',

                                                   True)
    @pytest.fixture
    def dialog_mock(self):
        return mock.patch.object(wx.MessageDialog, "__init__")

    @pytest.fixture
    def mock_brush_radius(self):
        return mock.patch.object(MainWindow, 'set_brush_radius', True)

    def test_get_image_name_from_path(self, setup, valid_rgb_image_path):
        """
        Test getting an image's name from its path

        :test_condition: Should be able to get the correct image name from
                         the given path

        :returns: None
        """
        controller = Controller()
        assert False

    def test_get_image_name_from_non_file_path(self, setup,
                                               directory_path):
        """

        Test geting an image name when a directory is given

        :test_condition: Should raise a ValueError

        :param directory_path: A path to a directory
        :returns: None
        """

        controller = Controller()
        assert False

    def test_get_image_name_from_invalid_path(self, setup,
                                              invalid_image_path):
        """
        Test getting the name of an image from a non-existant path

        :test_condition: Should raise an exception.

        :param invalid_image_path: A non-existant image path
        :returns: None
        """

        assert False

    def test_next_patch_valid_index_displayable(self, setup):
        """
        Test moving to the next patch when the current patch is not the last
        patch in the list of patches and the next patch is displayable

        :test_condition: The controller.current_patch is incremented by one

        :returns: None
        """

        assert False

    def test_next_patch_valid_index_not_displayable(self, setup):
        """
        Test moving to the next patch when the current patch is not the last
        patch in the list of patches and the next patch is not displayable

        :test_condition: The controller.current_patch is incremented by more
                         than one

        :returns: None
        """

        assert False


    def test_next_patch_invalid_index(self, mocker, setup, dialog_mock):
        """
        Test moving to the next patch when the current patch is the last patch
        in the list of patches

        :test_condition: A dialog box is created and the current_patch is the
                         same as it was before

        :returns: None
        """
        spy = mocker.spy(wx.MessageDialog, '__init__')

        spy.assert_called_once()

        controller = Controller()

        assert False

    def test_prev_patch_valid_index_displayable(self, setup):
        """
        Test moving to the previous patch when the current patch is greater
        than 0 and the previous patch is displayable

        :test_condition: The controller.current_patch is decremented by 1

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_prev_patch_valid_index_not_displayable(self, setup):
        """
        Test moving to the previous patch when the current patch is greater
        than 0 and the previous patch is not displayable

        :test_condition: The controller.current_patch is decremented by more
                         than 1

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_prev_patch_invalid_index(self, setup):
        """
        Test moving to thre previous patch when the current patch is 0

        :test_condition: The current_patch remains at 0

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_change_mode_thresh(self, setup, mock_brush_radius):
        """
        Test changing the mode to Threshold

        :test_condition: The current mode is set to Mode.THRESHOLD and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """

        assert False

    def test_change_mode_add_region(self, setup, mock_brush_radius):
        """
        Test changing the mode to add region

        :test_condition: The current mode is set to Mode.ADD_REGION and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """

        assert False

    def test_change_mode_remove_region(self, setup, mock_brush_radius):
        """
        Test changing the mode to remove region

        :test_condition: The current mode is set to Mode.REMOVE_REGION and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """

        assert False

    def test_change_mode_no_root_activate(self, setup):
        """
        Test changing the mode to NO ROOT

        :test_condition:  The mask of the current patch is all 0

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_no_root_activate(self, setup):
        """
        Test calling no_root activate

        :test_condition: The mask of the current patch is all 0

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_handle_mouse_wheel_threshold(self, setup):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.THRESHOLD

        :test_condition: The adjust threshold function is called

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_handle_mouse_wheel_add_region(self, setup):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.ADD_REGION

        :test_condition: The adjust_add_region_brush function is called

        :param setup: The setup fixture
        :returns: None
        """

        assert false

    def test_handle_mouse_wheel_remove_region(self, setup):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.REMOVE_REGION

        :test_condition: The adjust_remove_region_brush funtion is called

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_handle_mouse_wheel_invalid(self, setup):
        """
        Test when the mouse wheel function is called and the current mode is
        invalid

        :test_condition: The function returns False

        :param setup: The setup fixture
        :returns: None
        """

        assert False


    def test_handle_left_click_add_region(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.ADD_REGION

        :test_condition: The patch.add_region_function is called with the given
                         position and the current add_region_radius

        :param setup: The setup fixture
        :returns: None
        """

        assert False


    def test_handle_left_click_remove_region(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.REMOVE_REGION

        :test_condition: The patch.remove_region functin is called with the
                         given position and the current remove_region_radius

        :param setup: The setup fixture
        :returns: None
        """

        assert False

    def test_handle_left_click_invalid_mode(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.THRESHOLD

        :test_condition: The function should return False

        :param setup: The setup fixture
        :returns: None
        """

        assert False


