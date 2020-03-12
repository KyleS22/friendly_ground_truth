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

from mock import MagicMock, PropertyMock

from friendly_ground_truth.controller.controller import Controller, Mode
from friendly_ground_truth.view.view import MainWindow
from friendly_ground_truth.model.model import Patch

from skimage import io
from skimage.color import rgb2gray


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
    def test_image_data(self):
        return rgb2gray(io.imread(os.path.abspath('tests/data/KyleS22.jpg')))

    @pytest.fixture
    def setup(self, mocker):

        self.mock_MW_init = mocker.patch.object(MainWindow, '__init__',
                                                lambda x, y: None)
        self.mock_MW_Show = mocker.patch.object(MainWindow, 'Show')

        self.mock_MW_set_brush_radius = mocker.patch.object(MainWindow,
                                                            'set_brush_radius')

        self.mock_MW_draw_brush = mocker.patch.object(MainWindow, 'draw_brush')
        self.mock_C_display_current_patch = mocker.\
            patch.\
            object(Controller, 'display_current_patch')

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

        name = controller.get_image_name_from_path(valid_rgb_image_path)

        assert 'KyleS22_mask.png' == name

    def test_get_image_name_from_non_file_path(self, setup,
                                               directory_path):
        """

        Test geting an image name when a directory is given

        :test_condition: Should raise a ValueError

        :param directory_path: A path to a directory
        :returns: None
        """

        controller = Controller()

        with pytest.raises(ValueError):
            controller.get_image_name_from_path(directory_path)

    def test_next_patch_valid_index_displayable(self, setup):
        """
        Test moving to the next patch when the current patch is not the last
        patch in the list of patches and the next patch is displayable

        :test_condition: The controller.current_patch is incremented by one

        :returns: None
        """

        controller = Controller()
        controller.current_patch = 0

        mock_patch = MagicMock()
        display_mock = PropertyMock(return_value=True)

        type(mock_patch).display = display_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch,
                                    mock_patch,  mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.next_patch()

        assert controller.current_patch == 1

    def test_next_patch_valid_index_not_displayable(self, setup):
        """
        Test moving to the next patch when the current patch is not the last
        patch in the list of patches and the next patch is not displayable

        :test_condition: The controller.current_patch is incremented by more
                         than one

        :returns: None
        """

        controller = Controller()
        controller.current_patch = 0

        mock_patch = MagicMock()
        display_mock = PropertyMock(return_value=True)

        type(mock_patch).display = display_mock

        mock_no_display_patch = MagicMock()
        false_display_mock = PropertyMock(return_value=False)

        type(mock_no_display_patch).display = false_display_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch,
                                    mock_no_display_patch,  mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.next_patch()

        assert controller.current_patch == 2

    def test_next_patch_invalid_index(self, mocker, setup):
        """
        Test moving to the next patch when the current patch is the last patch
        in the list of patches

        :test_condition: A dialog box is created and the current_patch is the
                         same as it was before

        :returns: None
        """
        mock_dialog = mocker.patch('wx.MessageDialog')
        controller = Controller()

        mock_patch = MagicMock()
        display_mock = PropertyMock(return_value=True)

        type(mock_patch).display = display_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch,
                                    mock_patch,  mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.current_patch = 2

        controller.next_patch()

        mock_dialog.assert_called()

        assert controller.current_patch == 2

    def test_prev_patch_valid_index_displayable(self, setup):
        """
        Test moving to the previous patch when the current patch is greater
        than 0 and the previous patch is displayable

        :test_condition: The controller.current_patch is decremented by 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_patch = 2

        mock_patch = MagicMock()
        display_mock = PropertyMock(return_value=True)

        type(mock_patch).display = display_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch,
                                    mock_patch,  mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.prev_patch()

        assert controller.current_patch == 1

    def test_prev_patch_valid_index_not_displayable(self, setup):
        """
        Test moving to the previous patch when the current patch is greater
        than 0 and the previous patch is not displayable

        :test_condition: The controller.current_patch is decremented by more
                         than 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_patch = 2

        mock_patch = MagicMock()
        display_mock = PropertyMock(return_value=True)

        type(mock_patch).display = display_mock

        mock_no_display_patch = MagicMock()
        false_display_mock = PropertyMock(return_value=False)

        type(mock_no_display_patch).display = false_display_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch,
                                    mock_no_display_patch,  mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.prev_patch()

        assert controller.current_patch == 0

    def test_prev_patch_invalid_index(self, setup):
        """
        Test moving to thre previous patch when the current patch is 0

        :test_condition: The current_patch remains at 0

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch, mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.prev_patch()

        assert controller.current_patch == 0

    def test_change_mode_thresh(self, setup, mocker):
        """
        Test changing the mode to Threshold

        :test_condition: The current mode is set to Mode.THRESHOLD and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.ADD_REGION

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        spy = mocker.spy(MainWindow, 'set_brush_radius')

        controller.change_mode(MainWindow.ID_TOOL_THRESH)

        spy.assert_called_once()

        assert controller.current_mode == Mode.THRESHOLD

    def test_change_mode_add_region(self, setup, mocker):
        """
        Test changing the mode to add region

        :test_condition: The current mode is set to Mode.ADD_REGION and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """
        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        spy = mocker.spy(MainWindow, 'set_brush_radius')

        controller.change_mode(MainWindow.ID_TOOL_ADD)

        spy.assert_called_once()

        assert controller.current_mode == Mode.ADD_REGION

    def test_change_mode_remove_region(self, setup, mocker):
        """
        Test changing the mode to remove region

        :test_condition: The current mode is set to Mode.REMOVE_REGION and
                         MainWindow.set_brush_radius is called once

        :param setup: The setup fixture
        :param mock_brush_radius: A fixture mocking the
                                  MainWindow.set_brush_radius function
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        spy = mocker.spy(MainWindow, 'set_brush_radius')

        controller.change_mode(MainWindow.ID_TOOL_REMOVE)

        spy.assert_called_once()

        assert controller.current_mode == Mode.REMOVE_REGION

    def test_change_mode_no_root_activate(self, setup, mocker):
        """
        Test changing the mode to NO ROOT

        :test_condition:  The no_root_activate function is called

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        spy = mocker.spy(controller, 'no_root_activate')

        controller.change_mode(MainWindow.ID_TOOL_NO_ROOT)

        spy.assert_called_once()

    def test_no_root_activate(self, setup):
        """
        Test calling no_root activate

        :test_condition: The patch clear_mask and overlay mask functions are
                         called

        :param setup: The setup fixture
        :returns: None
        """
        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        controller.no_root_activate()

        mock_patch.clear_mask.assert_called()
        mock_patch.overlay_mask.assert_called()

    def test_handle_mouse_wheel_threshold(self, setup, mocker):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.THRESHOLD

        :test_condition: The adjust threshold function is called

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        mock_patch = MagicMock()
        thresh_mock = PropertyMock(return_value=0.5)

        type(mock_patch).thresh = thresh_mock

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        spy = mocker.spy(controller, 'adjust_threshold')

        controller.handle_mouse_wheel(-1)

        spy.assert_called_once_with(-1)

    def test_handle_mouse_wheel_add_region(self, setup, mocker):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.ADD_REGION

        :test_condition: The adjust_add_region_brush function is called

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.ADD_REGION

        spy = mocker.spy(controller, 'adjust_add_region_brush')

        controller.handle_mouse_wheel(-1)

        spy.assert_called_once_with(-1)

    def test_handle_mouse_wheel_remove_region(self, setup, mocker):
        """
        Test when the mouse wheel function is called and the current mode is
        Mode.REMOVE_REGION

        :test_condition: The adjust_remove_region_brush funtion is called

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.REMOVE_REGION

        spy = mocker.spy(controller, 'adjust_remove_region_brush')

        controller.handle_mouse_wheel(-1)

        spy.assert_called_once_with(-1)

    def test_handle_mouse_wheel_invalid(self, setup):
        """
        Test when the mouse wheel function is called and the current mode is
        invalid

        :test_condition: The function returns False

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.NO_ROOT

        result = controller.handle_mouse_wheel(-1)

        assert False is result

    def test_handle_left_click_add_region(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.ADD_REGION

        :test_condition: The patch.add_region_function is called with the given
                         position and the current add_region_radius

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.ADD_REGION

        mock_patch = MagicMock()

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        position = (1, 2)
        radius = controller.add_region_radius

        controller.handle_left_click(position)

        mock_patch.add_region.assert_called_with(position, radius)

    def test_handle_left_click_remove_region(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.REMOVE_REGION

        :test_condition: The patch.remove_region functin is called with the
                         given position and the current remove_region_radius

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.REMOVE_REGION

        mock_patch = MagicMock()

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        position = (1, 2)
        radius = controller.remove_region_radius

        controller.handle_left_click(position)

        mock_patch.remove_region.assert_called_with(position, radius)

    def test_handle_left_click_invalid_mode(self, setup):
        """
        Test when the left mouse button is clicked and the current mode is
        Mode.THRESHOLD

        :test_condition: The function should return False

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        result = controller.handle_left_click((0, 0))
        assert False is result

    def test_handle_left_release_add_region(self, setup):
        """
        Test when the mouse is released and the current mode is Mode.ADD_REGION

        :test_condition:  The function returns True

        :param setup: The setup ficture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.ADD_REGION

        result = controller.handle_left_release()

        assert True is result

    def test_handle_left_release_remove_region(self, setup):
        """
        Test when the mouse is released and the current mode is
        Mode.REMOVE_REGION

        :test_condition: The function returns True

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.REMOVE_REGION

        result = controller.handle_left_release()

        assert True is result

    def test_handle_left_release_invalid_mode(self, setup):
        """
        Test when the mouse is released and the current mode is not ADD or
        REMOVE REGION

        :test_condition: The function returns False

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        result = controller.handle_left_release()
        assert False is result

    def test_handle_motion_add_region(self, setup):
        """
        Test when the mouse is moved and the current mode is Mode.ADD_REGION

        :test_condition: The patch add_region function is called with the given
                         position and the current add_region_radius

        :param setup: The setip fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.ADD_REGION

        mock_patch = MagicMock()

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        position = (1, 2)
        radius = controller.add_region_radius

        controller.handle_motion(position)

        mock_patch.add_region.assert_called_with(position, radius)

    def test_handle_motion_remove_region(self, setup, mocker):
        """
        Test when the mouse is moved and the current mode is Mode.REMOVE_REGION

        :test_condition: The patch remove_region function is called with the
                         given position and the current remove_region_radius

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.REMOVE_REGION

        mock_patch = MagicMock()

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[mock_patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        position = (1, 2)
        radius = controller.remove_region_radius

        controller.handle_motion(position)

        mock_patch.remove_region.assert_called_with(position, radius)

    def test_handle_motion_invalid_mode(self, setup):
        """
        Test when the mouse is moved and the current mode is not ADD or REMOVE
        REGION

        :test_condition: Should return False

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        controller.current_mode = Mode.THRESHOLD

        result = controller.handle_motion((0, 0))

        assert False is result

    def test_adjust_threshold_positive_rot_valid_thresh(self, setup,
                                                        test_image_data):
        """
        Test when the mouse wheel has a positive rotation in Mode.THRESHOLD
        and the threshold is greater than 0
        :test_condition: The patches thresh value should be decreased by 0.01

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        patch = Patch(test_image_data, (0, 0))
        patch.thresh = 0.5

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        old_threshold = controller\
            .image.patches[controller.current_patch].thresh

        controller.adjust_threshold(1)

        new_patch = controller.image.patches[controller.current_patch]

        assert (old_threshold - 0.01) == new_patch.thresh

    def test_adjust_threshold_positive_rot_invalid_thresh(self, setup,
                                                          test_image_data):
        """
        Test when the mouse wheel has a positive rotation in Mode.THRESHOLD
        and the threshold is smaller than or equal to 0

        :test_condition: The patches thresh value should not be changed

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        patch = Patch(test_image_data, (0, 0))
        patch.thresh = 0.0

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        old_threshold = controller\
            .image.patches[controller.current_patch].thresh

        controller.adjust_threshold(1)

        new_patch = controller.image.patches[controller.current_patch]

        assert old_threshold == new_patch.thresh

    def test_adjust_threshold_negative_rot_invalid_thresh(self, setup,
                                                          test_image_data):
        """
        Test when the mouse wheel has a negative rotation in Mode.THRESHOLD
        and the threshold is greater than or equal to one

        :test_condition: The patches thresh value should not be changed

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        patch = Patch(test_image_data, (0, 0))
        patch.thresh = 1.0

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        old_threshold = controller\
            .image.patches[controller.current_patch].thresh

        controller.adjust_threshold(-1)

        new_patch = controller.image.patches[controller.current_patch]

        assert old_threshold == new_patch.thresh

    def test_adjust_threshold_negative_rot_valid_thresh(self, setup,
                                                        test_image_data):
        """
        Test when the mouse wheel has a negative rotation in Mode.THRESHOLD
        and the threshold is less than one

        :test_condition: The patches thresh value should be increased by 0.01

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()
        patch = Patch(test_image_data, (0, 0))
        patch.thresh = 0.5

        mock_image = MagicMock()
        patches_mock = PropertyMock(return_value=[patch])

        type(mock_image).patches = patches_mock

        controller.image = mock_image

        old_threshold = controller\
            .image.patches[controller.current_patch].thresh

        controller.adjust_threshold(-1)

        new_patch = controller.image.patches[controller.current_patch]

        assert old_threshold != new_patch.thresh
        assert (old_threshold + 0.01) == new_patch.thresh

    def test_adjust_add_region_brush_positive_rot(self, setup):
        """
        Test when the mouse wheel has a positive rotation in Mode.ADD_REGION

        :test_condition: The add_region_radius is increased by 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()

        old_add_radius = controller.add_region_radius

        controller.adjust_add_region_brush(1)

        assert controller.add_region_radius != old_add_radius
        assert (controller.add_region_radius - 1) == old_add_radius

    def test_adjust_add_region_brush_negative_rot(self, setup):
        """
        Test when the mouse wheel has a negative rotation in Mode.ADD_REGION

        :test_condition: The add_region_radius is decreased by 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()

        old_add_radius = controller.add_region_radius

        controller.adjust_add_region_brush(-1)

        assert controller.add_region_radius != old_add_radius
        assert (controller.add_region_radius + 1) == old_add_radius

    def test_adjust_remove_region_brush_positive_rot(self, setup):
        """
        Test when the mouse wheel has a positive rotation in Mode.REMOVE_REGION

        :test_condition: The remove_region_radius is increased by 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()

        old_remove_radius = controller.remove_region_radius

        controller.adjust_remove_region_brush(1)

        assert controller.remove_region_radius != old_remove_radius
        assert (controller.remove_region_radius - 1) == old_remove_radius

    def test_adjust_remove_region_brush_negative_rot(self, setup):
        """
        Test when the mouse wheel has a negative rotation in Mode.REMOVE_REGION

        :test_condition: The remove_region_radius is decreased by 1

        :param setup: The setup fixture
        :returns: None
        """

        controller = Controller()

        old_remove_radius = controller.remove_region_radius

        controller.adjust_remove_region_brush(-1)

        assert controller.remove_region_radius != old_remove_radius
        assert (controller.remove_region_radius + 1) == old_remove_radius
