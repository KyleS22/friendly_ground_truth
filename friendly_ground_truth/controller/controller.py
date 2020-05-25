"""
File Name: controller.py

Authors: Kyle Seidenthal

Date: 13-05-2020

Description: Main controller for the application

"""
from friendly_ground_truth.view.main_window import MainWindow
from friendly_ground_truth.view.preview_window import PreviewWindow
from friendly_ground_truth.controller.tools import (ThresholdTool,
                                                    AddRegionTool,
                                                    RemoveRegionTool,
                                                    NoRootTool,
                                                    FloodAddTool,
                                                    FloodRemoveTool,
                                                    PreviousPatchTool,
                                                    NextPatchTool,
                                                    UndoTool,
                                                    RedoTool)

from friendly_ground_truth.controller.undo_manager import UndoManager
from friendly_ground_truth.model.model import Image

from skimage import segmentation, img_as_ubyte

import os
import copy
import json

import tkinter.filedialog
import tkinter.messagebox

import numpy as np

import logging
module_logger = logging.getLogger('friendly_gt.controller.controller')

PREFERENCES_PATH = "./user_preferences.json"
DEFAULT_PREFS = {'theme': 'Light'}


class Controller():
    """
    Main controller for the application.

    Attributes:
        image_tools: A dictionary of tools keyed by their id
    """
    CONTEXT_TRANSPARENCY = 100
    NUM_PATCHES = 10

    def __init__(self, root):
        """
        Create a Controller object

        Args:
            root: The tk Root

        Returns:
            A controller object

        Postconditions:
            The main application window is started
        """
        # ------------------------------------
        # Private Attributes
        # -----------------------------------

        # The root tkinter object
        self._root = root
        # For logging
        self._logger = logging.getLogger('friendly_gt.controller.'
                                         'controller.Controller')
        # The last directory used to load an image
        self._last_load_dir = None
        # The last directory used to save an image
        self._last_save_dir = None

        # Image containing neighbouring patches
        self._context_img = None

        # For managing undo operations
        self._undo_manager = UndoManager()
        # A dictionary of image tools
        self._image_tools = {}
        self._init_tools()

        # Initialize the main window
        self._main_window = MainWindow(self._root, self)

        # The path to the current image
        self._image_path = None

        # The current image
        self._image = None

        # The index of the current patch in _image.patches
        self._current_patch_index = 0

        # Whether the mask has been saved
        self._mask_saved = False

        # The current tool in use
        self._current_tool = None

        # The offset of the current patch within the context image
        self._patch_offset = (0, 0)

        # Whether the mask preview has been shown or not
        self._previewed = False

        # Disable the redo button for now
        self._main_window.disable_button(self._redo_id)
        self._main_window.disable_button(self._undo_id)

    @property
    def image_tools(self):
        return self._image_tools

    # ===================================================
    # PUBLIC FUNCTIONS
    # ===================================================
    def load_new_image(self):
        """
        Load a new image with a file dialog.


        Returns:
            None
        """

        self._context_img = None
        filetypes = [("TIF Files", "*.tif"), ("TIFF Files", "*.tiff"),
                     ("PNG Files", "*.png"), ("JPEG Files", "*.jpg")]

        if self._last_load_dir is None:
            initial_dir = os.path.expanduser("~")
        else:
            initial_dir = self._last_load_dir

        file_name = tkinter.filedialog.askopenfilename(filetypes=filetypes,
                                                       initialdir=initial_dir)

        if file_name is None or file_name == ():
            return

        self._last_load_dir = os.path.split(file_name)[0]

        self._image_path = file_name

        try:
            self._main_window.start_progressbar(self.NUM_PATCHES ** 2)
            self._image = Image(file_name, 10, self._update_progressbar)

        except FileNotFoundError:
            self._logger.exception("There was a problem loading the image.")
            return

        self._current_patch_index = 0

        self._display_current_patch()
        self._main_window.update_image_indicator(self._image_path)

    def save_mask(self):
        """
        Save the finished image mask.


        Returns:
            None
        """

        if not self._previewed:
            self._show_saved_preview()
            return

        self._mask_saved = True

        if self._last_save_dir is None:
            initial_dir = os.path.expanduser("~")
        else:
            initial_dir = self._last_save_dir

        dir_path = tkinter.filedialog.askdirectory(initialdir=initial_dir)

        if dir_path is None:
            return

        image_name = self._get_image_name_from_path(self._image_path)
        # labels_name = self._get_landmark_name_from_path(self._image_path)

        mask_pathname = os.path.join(dir_path, image_name)
        # label_pathname = os.path.join(dir_path, labels_name)

        try:
            self._image.export_mask(mask_pathname)
            # self._image.export_labels(label_pathname)

            tkinter.messagebox.showinfo("Image Mask Saved!",
                                        "Image Mask Saved!")

        except IOError:
            self._logger.error("Could not save file!")

    def set_preferences(self, preferences):
        """
        Set the current preferences for the application.

        Args:
            preferences: A dictionary of preferences and their values.

        Returns:
            None
        """
        theme = preferences['theme']

        self._main_window.set_theme(theme)

    def load_preferences(self):
        """
        Load the preferences saved in the preferences file.


        Returns:
            A dictionary containing the user's preferences.
        """
        if not os.path.exists(PREFERENCES_PATH):
            return DEFAULT_PREFS

        with open(PREFERENCES_PATH, 'r') as fin:
            preferences = json.load(fin)

        return preferences

    def save_preferences(self, preferences):
        """
        Save the user preferences.

        Args:
            preferences: A dictionary containing the user preferences.

        Returns:
            None
        """

        with open(PREFERENCES_PATH, 'w') as fout:
            json.dump(preferences, fout)

    def activate_tool(self, id):
        """
        Activate the given tool id.

        Args:
            id: The id of the tool.

        Returns:
            None

        Postcondition:
            The current tool is set to the tool matching the id
            Any activation functionality of the tool is performed.
        """
        if self._image is None:
            return

        tool = self.image_tools[id]
        tool.image = self._image
        tool.patch = self._image.patches[self._current_patch_index]

        old_tool = None

        if not tool.persistant:
            old_tool = self._current_tool

        self._current_tool = tool

        tool.on_activate(self._current_patch_index)

        if old_tool is not None:
            self._current_tool = old_tool
            tool = old_tool

        tool.lock_undos()
        # self._display_current_patch()
        self._main_window.update_info_panel(tool)
        self._main_window.set_canvas_cursor(tool.cursor)
        tool.unlock_undos()

        if not self._undo_manager.undo_empty:
            self._main_window.enable_button(self._undo_id)

    def adjust_tool(self, direction):
        """
        Adjust the current tool.

        Args:
            direction: An integer, positive is up, negative is down.

        Returns:
            None
        """
        self._current_tool.on_adjust(direction)
        # self._display_current_patch()

        if not self._undo_manager.undo_empty:
            self._main_window.enable_button(self._undo_id)

    def click_event(self, pos):
        """
        A click event in the main window has occured.

        Args:
            pos: The position of the event.

        Returns:
            None
        """
        # Correct for offset in context image
        pos = pos[0] - self._patch_offset[1], pos[1] - self._patch_offset[0]

        # Need to invert the position, because tkinter coords are backward from
        # skimage
        pos = round(pos[1]-1), round(pos[0]-1)

        self._logger.debug("Click Event: {}".format(pos))

        if self._current_tool is not None:
            self._current_tool.on_click(pos)

        if not self._undo_manager.undo_empty:
            self._main_window.enable_button(self._undo_id)

    def drag_event(self, pos):
        """
        A click event in the main window has occured/

        Args:
            pos: The position of the event.

        Returns:
            None
        """
        # Correct for offset in context image
        pos = pos[0] - self._patch_offset[1], pos[1] - self._patch_offset[0]

        # Need to invert the position, because tkinter coords are backward from
        # skimage
        pos = round(pos[1]-1), round(pos[0]-1)

        self._current_tool.on_drag(pos)

        if not self._undo_manager.undo_empty:
            self._main_window.enable_button(self._undo_id)

    # ===================================================
    # Private Functions
    # ===================================================

    def _init_tools(self):
        """
        Create all the required tools.


        Returns:
            None

        Postconditions:
            self._image_tools will be created as a dictionary of id, tool pairs
        """

        image_tools = {}

        thresh_tool = ThresholdTool(self._undo_manager)
        image_tools[thresh_tool.id] = thresh_tool

        add_reg_tool = AddRegionTool(self._undo_manager)
        add_reg_tool.bind_brush(self._brush_size_callback)
        image_tools[add_reg_tool.id] = add_reg_tool

        rem_reg_tool = RemoveRegionTool(self._undo_manager)
        rem_reg_tool.bind_brush(self._brush_size_callback)
        image_tools[rem_reg_tool.id] = rem_reg_tool

        flood_add_tool = FloodAddTool(self._undo_manager)
        image_tools[flood_add_tool.id] = flood_add_tool

        flood_rem_tool = FloodRemoveTool(self._undo_manager)
        image_tools[flood_rem_tool.id] = flood_rem_tool

        no_root_tool = NoRootTool(self._undo_manager,
                                  self._next_patch_callback)
        image_tools[no_root_tool.id] = no_root_tool

        prev_patch_tool = PreviousPatchTool(self._undo_manager,
                                            self._prev_patch_callback)
        image_tools[prev_patch_tool.id] = prev_patch_tool

        next_patch_tool = NextPatchTool(self._undo_manager,
                                        self._next_patch_callback)
        image_tools[next_patch_tool.id] = next_patch_tool

        undo_tool = UndoTool(self._undo_manager,
                             self._undo_callback)
        image_tools[undo_tool.id] = undo_tool
        self._undo_id = undo_tool.id

        redo_tool = RedoTool(self._undo_manager,
                             self._redo_callback)
        image_tools[redo_tool.id] = redo_tool
        self._redo_id = redo_tool.id

        for id in image_tools.keys():
            image_tools[id].bind_to(self._display_current_patch)

        self._image_tools = image_tools

    def _next_patch_callback(self, patch, index):
        """
        Called when the next patch is determined.

        Args:
            patch: The next patch.
            index: The index in the patches list of the patch.

        Returns:
            None
        """
        self._logger.debug("Next patch {}.".format(index))

        if patch is None or index == -1:
            self._display_current_patch()
            self.save_mask()
            return

        cur_patch = self._image.patches[self._current_patch_index]
        cur_patch.undo_history = copy.deepcopy(self._undo_manager)

        self._context_img = None
        self._current_patch_index = index

        cur_patch = self._image.patches[self._current_patch_index]

        if cur_patch.undo_history is None:
            self._undo_manager = UndoManager()
        else:
            self._undo_manager = copy.deepcopy(cur_patch.undo_history)

        for key in self._image_tools.keys():
            self._image_tools[key].patch = patch
            self._image_tools[key].undo_manager = self._undo_manager

        self._display_current_patch(new=True)

        if self._undo_manager.undo_empty:
            self._main_window.disable_button(self._undo_id)
        else:
            self._main_window.enable_button(self._undo_id)

        if self._undo_manager.redo_empty:
            self._main_window.disable_button(self._redo_id)
        else:
            self._main_window.enable_button(self._redo_id)

    def _prev_patch_callback(self, patch, index):
        """
        Called when the previous patch is determined.

        Args:
            patch: The previous patch
            index: The index of that patch in the list of patches.

        Returns:
            None
        """

        if patch is None or index == -1:
            return

        cur_patch = self._image.patches[self._current_patch_index]
        cur_patch.undo_history = copy.deepcopy(self._undo_manager)

        self._context_img = None
        self._current_patch_index = index

        cur_patch = self._image.patches[self._current_patch_index]

        if cur_patch.undo_history is None:
            self._undo_manager = UndoManager()
        else:
            self._undo_manager = copy.deepcopy(cur_patch.undo_history)

        for key in self._image_tools.keys():
            self._image_tools[key].patch = patch
            self._image_tools[key].undo_manager = self._undo_manager

        self._display_current_patch(new=True)

        self._main_window.disable_button(self._undo_id)
        self._main_window.disable_button(self._redo_id)

    def _undo_callback(self, patch, string):
        """
        Called when undo is done.

        Args:
            patch: The patch returned from the undo stack.
            string: The string for that patch.

        Returns:
            None
        """
        if patch is None:
            return

        current_patch = self._image.patches[self._current_patch_index]

        self._undo_manager.add_to_redo_stack(copy.deepcopy(current_patch),
                                             string)

        self._main_window.enable_button(self._redo_id)

        if self._undo_manager.undo_empty:
            self._main_window.disable_button(self._undo_id)

        self._image.patches[self._current_patch_index] = patch

        for key in self._image_tools.keys():
            self._image_tools[key].lock_undos()
            self._image_tools[key].patch = patch

    def _redo_callback(self, patch, string):
        """
        Called when redo is done.

        Args:
            patch: The patch returned from the redo stack.
            string: The string for that patch.

        Returns:
            None
        """
        if patch is None:
            return

        current_patch = self._image.patches[self._current_patch_index]

        self._undo_manager.add_to_undo_stack(copy.deepcopy(current_patch),
                                             string)

        if self._undo_manager.redo_empty:
            self._main_window.disable_button(self._redo_id)

        self._main_window.enable_button(self._undo_id)

        self._image.patches[self._current_patch_index] = patch

        for key in self._image_tools.keys():
            self._image_tools[key].lock_undos()
            self._image_tools[key].patch = patch

    def _display_current_patch(self, new=False):
        """
        Display the current patch.


        Returns:
            None

        Postconditions:
            The main window's canvas will display the given image.
        """
        if self._image is None:
            return

        patch = self._image.patches[self._current_patch_index]
        img = self._get_context_patches(patch)

        self._main_window.show_image(img, new=new,
                                     patch_offset=self._patch_offset)

        if self._current_tool is not None:
            self._current_tool.unlock_undos()
        if self._undo_manager.undo_empty:
            self._main_window.disable_button(self._undo_id)
        else:
            self._main_window.enable_button(self._undo_id)

    def _brush_size_callback(self, radius):
        """
        Called when a brush tool is updated.

        Args:
            radius: The new brush radius.

        Returns:
            None
        """
        self._main_window.set_canvas_brush_size(radius)

    def _get_context_patches(self, patch):
        """
        Get the patches immediately surrounding the current patch and place
        them in a larger image.

        Args:
            patch: The current patch

        Returns:
            An image for display.
        """

        # Find the neighbouring patches
        index = patch.patch_index

        if self._context_img is not None:
            patch = self._image.patches[self._current_patch_index]
            r_start = self._patch_offset[0]
            r_end = r_start + patch.overlay_image.shape[0]
            c_start = self._patch_offset[1]
            c_end = c_start + patch.overlay_image.shape[1]

            o_img = patch.overlay_image
            o_img = np.dstack((o_img, np.full(o_img.shape[0:-1],
                               255, dtype=o_img.dtype)))

            self._context_img[r_start:r_end, c_start:c_end] = o_img
            return self._context_img

        neighbouring_indices = []

        start_i = index[0] - 1
        start_j = index[1] - 1

        num_rows = 0
        num_cols = 0

        for i in range(start_i, start_i + 3):

            if i < 0 or i >= self._image.num_patches:
                continue
            for j in range(start_j, start_j + 3):
                if j < 0 or j >= self._image.num_patches:
                    continue

                neighbouring_indices.append((i, j))

                if num_rows == 0:
                    num_cols += 1
            num_rows += 1

        neighbouring_patches = []
        drawable_patch_index = None  # Index of our patch in this list

        # TODO: This could be more efficient I'm sure
        for i in neighbouring_indices:
            for patch in self._image.patches:
                if patch.patch_index == i:
                    o_img = patch.overlay_image

                    if i == index:
                        o_img = np.dstack((o_img, np.full(o_img.shape[0:-1],
                                           255,
                                           dtype=o_img.dtype)))
                        drawable_patch_index = neighbouring_indices.index(i)
                    else:
                        o_img = np.dstack((o_img, np.full(o_img.shape[0:-1],
                                           self.CONTEXT_TRANSPARENCY,
                                           dtype=o_img.dtype)))

                    neighbouring_patches.append(o_img)

        # Layer them into a numpy array
        img_shape = (patch.overlay_image.shape[0] * num_rows,
                     patch.overlay_image.shape[1] * num_cols, 4)
        img = np.zeros(img_shape, dtype=np.ubyte)

        col_num = 0
        row_num = 0

        i = 0
        for patch in neighbouring_patches:
            r, c = row_num, col_num
            r = r * patch.shape[0]
            c = c * patch.shape[1]
            img[r:r+patch.shape[0],
                c:c+patch.shape[1]] += patch
            if i == drawable_patch_index:
                self._patch_offset = (r, c)

            col_num += 1

            if col_num == num_cols:
                col_num = 0
                row_num += 1

            i += 1

        self._context_img = img
        return img

    def _update_progressbar(self):
        """
        Update the progressbar popup


        Returns:
            None

        Postconditions:
            The progressbar will be incremented.
        """
        self._main_window.progress_popup.update()
        self._main_window.load_progress += self._main_window.progress_step
        self._main_window.load_progress_var\
            .set(self._main_window.load_progress)

        if self._main_window.load_progress >= self.NUM_PATCHES ** 2:
            self._main_window.progress_popup.destroy()

    def _show_saved_preview(self):
        """
        Display a preview of the saved mask overlaid with the image.


        Returns:
            None

        Postconditions:
            A window displaying the image and mask is shown.
        """

        self._previewed = True

        img = self._image.image
        mask = self._image.mask

        overlay = segmentation.mark_boundaries(img, mask)

        overlay = img_as_ubyte(overlay)

        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        overlay = overlay[rmin:rmax, cmin:cmax]

        PreviewWindow(overlay, self, self._main_window.style)

    def _get_image_name_from_path(self, path):
        """
        Get the name of the image from its original path.

        Args:
            path: The path to the original image.

        Returns:
            The name to save the image mask as.
        """
        if os.path.isdir(path):
            raise ValueError("Cannot get image name from a directory.")

        basename = os.path.basename(path)

        return os.path.splitext(basename)[0] + '_mask.png'
