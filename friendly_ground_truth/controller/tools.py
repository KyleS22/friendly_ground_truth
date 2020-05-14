"""
File Name: tools.py

Authors: Kyle Seidenthal

Date: 11-05-2020

Description: Definitions of tools that can be used in Friendly Ground Truth

"""
import logging
import copy

from friendly_ground_truth.view.icons.icon_strings import (threshold_icon,
                                                           add_region_icon,
                                                           remove_region_icon,
                                                           no_root_icon,
                                                           flood_add_icon,
                                                           flood_remove_icon,
                                                           prev_patch_icon,
                                                           next_patch_icon,
                                                           undo_icon,
                                                           redo_icon)

module_logger = logging.getLogger('friendly_gt.controller.tools')


class FGTTool():
    """
    A class representing a tool that can be used on the image.

    Attributes:
        name: The name of the tool
        icon_string: A 64 bit encoded string representing an icon image
        id: A unique id for the tool
        persistant: Whether the tool stays activated when it has been activated
        key_mapping: The keyboard shortcut string for this tool
        activation_callback: A function to call when the activate functiion is
                             finished
    """

    def __init__(self, name, icon_string, id,  undo_manager,
                 key_mapping, cursor='none', persistant=True,
                 activation_callback=None):
        """
        Initialize the object

        Args:
            name: The name of the tool
            icon_string: A bytestring representing the icon for the tool
            id: A unique id for the tool
            cursor: The default cursor for this tool.  Default value is 'none'
            undo_manager: The controller's undo manager
            key_mapping: The keyboard shortcut string for this tool
            activation_callback: A function to call when the activate function
                                 is finished
        """
        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.FGTTool')

        self._name = name
        self._icon_string = icon_string
        self._id = id
        self._cursor = cursor
        self._undo_manager = undo_manager
        self._key_mapping = key_mapping
        self._activation_callback = activation_callback

    @property
    def name(self):
        return self._name

    @property
    def icon_string(self):
        return self._icon_string

    @icon_string.setter
    def icon_string(self, string):
        self._icon_string = string

    @property
    def id(self):
        return self._id

    @property
    def cursor(self):
        return self._cursor

    @property
    def patch(self):
        return self._patch

    @patch.setter
    def patch(self, patch):
        self._patch = patch

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def persistant(self):
        return self._persistant

    @property
    def key_mapping(self):
        return self._key_mapping

    def on_adjust(self, direction):
        """
        What happens when the tool is adjusted.

        Args:
            direction: An integer, positive is up, negative is down

        Returns:
            None
        """
        pass

    def on_click(self, position):
        """
        What happens for mouse clicks.

        Args:
            position: The position of the click

        Returns:
            None
        """
        pass

    def on_drag(self, position):
        """
        What happens for click and drag.

        Args:
            position: The position of the mouse

        Returns:
            None
        """
        pass

    def on_activate(self, current_patch_num):
        """
        What happens when the tool is activated.

        Args:
            current_patch_num: The index of the current patch in the patches
                               list
        Returns:
            None

        Postconditions:
            The activation callback may be called.
        """
        pass


class ThresholdTool(FGTTool):
    """
    Tool representing a threshold action.

    Attributes:
        threshold: The value of the threshold. Between 0 and 1.
        increment: The amount to change the threshold by when adjusting
    """

    def __init__(self, undo_manager):

        super(ThresholdTool, self)\
            .__init__("Threshold Tool", threshold_icon, 1,
                      undo_manager, "T", cursor='arrow', persistant=False,
                      activation_callback=None)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.ThresholdTool')

        self._threshold = 0
        self._increment = 0.01
        self._patch = None

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, value):
        if value <= 1 and value >= 0:
            self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                                 'threshold_adjust')
            self._threshold = value
            self._patch.threshold = value

    @property
    def increment(self):
        return self._increment

    @increment.setter
    def increment(self, value):
        self._increment = value

    @FGTTool.patch.setter
    def patch(self, patch):
        self._patch = patch
        self._threshold = patch.threshold

    def _adjust_threshold(self, direction):
        """
        Adjust the current threshold

        Args:
            direction: An integer, positive indicates increasing threshold,
                       negative idicates decreasing threshold

        Returns:
            None, the patch threshold will be set accordingly
        """

        if direction > 0:
            self.threshold += self.increment
        else:
            self.threshold -= self.increment

    def on_adjust(self, direction):
        """
        Adjust the threshold in the correct direction

        Args:
            direction: The direction, an integer
                       Negative is down, positive is up

        Returns:
            None
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "threshold_adjust")
        self._adjust_threshold(direction)


class AddRegionTool(FGTTool):
    """
    A tool acting as a paint brush for adding regions to the mask

    Attributes:
        brush_radius: The current radius of the brush
    """

    def __init__(self, undo_manager):
        super(AddRegionTool, self)\
            .__init__("Add Region Tool", add_region_icon, 2,
                      undo_manager, "A", cursor='brush', persistant=True)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.AddRegionTool')

        self._brush_radius = 15

    @property
    def brush_radius(self):
        return self._brush_radius

    @brush_radius.setter
    def brush_radius(self, value):
        if value >= 0:
            self._brush_radius = value

    def on_adjust(self, direction):
        """
        Adust the brush size according to the direction.

        Args:
            direction: An integer, positive means up, negative means down.

        Returns:
            None
        """
        if direction > 0:
            self.brush_radius += 1
        else:
            self.brush_radius -= 1

    def on_click(self, position):
        """
        What to do on mouse clicks.

        Args:
            position: The position of the mouse.

        Returns:
            None
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "add_region")

        self._draw(position)

    def on_drag(self, position):
        """
        What to do when clicking and dragging

        Args:
            position: The position of the mouse.

        Returns:
            None
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "add_region_adjust")
        self._draw(position)

    def _draw(self, position):
        """
        Draw a circle at the given position.  Uses the brush_radius property.

        Args:
            position: (x, y) coordinates to draw at.

        Returns:
            None

        Postcondition:
            The mask at the given position will be filled in.
        """
        self.patch.add_region(position, self.brush_radius)


class RemoveRegionTool(FGTTool):
    """
    A tool acting as a paint brush for removing regions from the mask

    Attributes:
        brush_radius: The current radius of the brush
    """

    def __init__(self, undo_manager):
        super(RemoveRegionTool, self)\
            .__init__("Remove Region Tool", remove_region_icon, 3,
                      undo_manager, "R", cursor="brush", persistant=True)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.RemoveRegionTool')

        self._brush_radius = 15

    @property
    def brush_radius(self):
        return self._brush_radius

    @brush_radius.setter
    def brush_radius(self, value):
        if value >= 0:
            self._brush_radius = value

    def on_adjust(self, direction):
        """
        Adust the brush size according to the direction.

        Args:
            direction: An integer, positive means up, negative means down.

        Returns:
            None
        """
        if direction > 0:
            self.brush_radius += 1
        else:
            self.brush_radius -= 1

    def on_click(self, position):
        """
        What to do on mouse clicks.

        Args:
            position: The position of the mouse.

        Returns:
            None
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "remove_region")

        self._draw(position)

    def on_drag(self, position):
        """
        What to do when clicking and dragging

        Args:
            position: The position of the mouse.

        Returns:
            None
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "remove_region_adjust")
        self._draw(position)

    def _draw(self, position):
        """
        Remove a circle at the given position.  Uses the brush_radius property.

        Args:
            position: (x, y) coordinates to draw at.

        Returns:
            None

        Postcondition:
            The mask at the given position will be removed.
        """

        self.patch.remove_region(position, self.brush_radius)


class NoRootTool(FGTTool):
    """
    A tool that marks a patch as having no foreground.
    """

    def __init__(self, undo_manager, next_patch_function):
        """
        Create the tool

        Args:
            undo_manager: The undo manager
            next_patch_function: The function to call to go to the next patch.
                                 Must have a patch and index parameter

        Returns:
            {% A thing %}
        """
        super(NoRootTool, self)\
            .__init__("No Root Tool", no_root_icon, 4,
                      undo_manager, "X", cursor='none', persistant=False,
                      activation_callback=next_patch_function)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.NoRootTool')

    def on_activate(self, current_patch_num):
        """
        What happens when the tool is activated.

        Args:
            current_patch_num: The index of the current patch in the patches
                               list
        Returns:
            None

        Postconditions:
            The foreground is removed from the patch, and the next patch is
            displayed.
        """
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             "no_root")

        self._no_root()
        patch, index = self._next_patch(current_patch_num)

        self._activation_callback(patch, index)

    def _no_root(self):
        """
        Clear the mask for this patch.


        Returns:
            None

        Postconditions:
            The mask for this patch is cleared.
        """
        self.patch.clear_mask()

    def _next_patch(self, current_patch_num):
        """
        Move to the next patch if it exists.

        Args:
            current_patch_num: The index of the current patch in the patches
                               list.

        Returns:
            A (patch, patch_num) tuple if there is a next patch.
            (None, -1) if there is not a next patch
        """
        patches = self._image.patches

        next_index = current_patch_num + 1

        if next_index < len(patches):
            self._undo_manager.clear_undos()
            return patches[next_index], next_index

        else:
            return None, -1


class FloodAddTool(FGTTool):
    """
    A tool that allows adding a region based on pixel tolerance.

    Attributes:
        tolerance: The tolerance for pixels to add to the region.
        increment: The amount that the tolerance increases by when using the
                   adjust method
    """

    def __init__(self, undo_manager):
        super(FloodAddTool, self)\
            .__init__("Flood Add Tool", flood_add_icon, 5,
                      undo_manager, "F", cursor='cross', persistant=True)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.FloodAddTool')

        self._tolerance = 0.05
        self._increment = 0.01

        self._prev_position = None

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        if value >= 0:
            self._tolerance = value

    @property
    def increment(self):
        return self._increment

    @increment.setter
    def increment(self, value):
        self._increment = value

    def on_click(self, position):
        """
        When the mouse is clicked, start the flood at the position/

        Args:
            position: The (x, y) coordinates of the place to start the flood.

        Returns:
            None
        """
        self._prev_position = position
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             'flood_add')
        self._add_region(position)

    def on_adjust(self, direction):
        """
        When the tool is adjusted, the tolerance is changed.

        Args:
            direction: An integer, positive means up, negative means down.

        Returns:
            None
        """

        if direction > 0:
            self.tolerance += self.increment
        else:
            self.tolerance -= self.increment

        self._add_region(self._prev_position)

    def _add_region(self, position):
        """
        Add a region at the given position, using the tolerance attribute.

        Args:
            position: (x, y) coordinates to start the flood.

        Returns:
            None

        Postconditions:
            A region will be added to the mask that matches the flooded region.
        """

        self.patch.flood_add(position, self.tolerance)


class FloodRemoveTool(FGTTool):
    """
    A tool that allows removing a region based on pixel tolerance.

    Attributes:
        tolerance: The tolerance for pixels to remove from the region.
    """

    def __init__(self, undo_manager):
        super(FloodRemoveTool, self)\
            .__init__("Flood Remove Tool", flood_remove_icon, 6,
                      undo_manager, "L", cursor='cross', persistant=True)

        self._logger = logging\
            .getLogger('friendly_gt.controller.tools.FloodRemoveTool')

        self._tolerance = 0.05
        self._increment = 0.01

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        if value > 0:
            self._tolerance = value

    @property
    def increment(self):
        return self._increment

    @increment.setter
    def increment(self, value):
        self._increment = value

    def on_click(self, position):
        """
        When the mouse is clicked, start the flood at the position.

        Args:
            position: The (x, y) coordinates of the place to start the flood.

        Returns:
            None
        """
        self._prev_position = position
        self._undo_manager.add_to_undo_stack(copy.deepcopy(self.patch),
                                             'flood_remove')
        self._remove_region(position)

    def on_adjust(self, direction):
        """
        When the tool is adjusted, the tolerance is changed.

        Args:
            direction: An integer, positive means up, negative means down.

        Returns:
            None
        """

        if direction > 0:
            self.tolerance += self.increment
        else:
            self.tolerance -= self.increment

        self._remove_region(self._prev_position)

    def _remove_region(self, position):
        """
        Remove a region at the given position, using the tolerance attribute.

        Args:
            position: (x, y) coordinates to start the flood.

        Returns:
            None

        Postconditions:
            A region will be removed to the mask that matches the
                flooded region.
        """

        self.patch.flood_remove(position, self.tolerance)


class PreviousPatchTool(FGTTool):
    """
    A Tool that moves to the previous patch for the current image.

    Attributes:
        image: The image to operate on
    """

    def __init__(self, undo_manager, prev_patch_function):
        """
        Create the tool.

        Args:
            undo_manager: The undo manager
            prev_patch_function: A function callback that takes in a patch and
                                 patch index representing the next patch

        Returns:
            A tool object
        """
        super(PreviousPatchTool, self)\
            .__init__("Previous Patch", prev_patch_icon, 7,
                      undo_manager, "Left Arrow", cursor='none',
                      persistant=False,
                      activation_callback=prev_patch_function)

    def on_activate(self, current_patch_num):
        """
        When the tool is activated, move to the previous patch.

        Args:
            current_patch_num: The index of the current patch in the patches
                               list

        Returns:
            None
        """
        patch, index = self._prev_patch(current_patch_num)
        self._activation_callback(patch, index)

    def _prev_patch(self, current_patch_num):
        """
        Move to the previous patch in the image.

        Args:
            current_patch_num: The index of the current patch.

        Returns:
            (patch, current_patch_index) if there is a previous patch
            (None, -1) if there is not a previous patch
        """

        patches = self._image.patches

        prev_index = current_patch_num - 1

        if prev_index >= 0:
            return patches[prev_index], prev_index

        else:
            return None, -1


class NextPatchTool(FGTTool):
    """
    A Tool that moves to the next patch for the current image.
    """

    def __init__(self, undo_manager, next_patch_function):
        """
        Create the tool.

        Args:
            undo_manager: The undo_manager for this tool.
            next_patch_function: A function callback that takes in a patch and
                                 index
        Returns:
            A tool object
        """
        super(NextPatchTool, self)\
            .__init__("Next Patch", next_patch_icon, 8,
                      undo_manager, "Right Arrow", cursor='none',
                      persistant=False,
                      activation_callback=next_patch_function)

    def on_activate(self, current_patch_num):
        """
        When the tool is activated, move to the next patch.

        Args:
            current_patch_num: The index of the current patch in the patches
                               list

        Returns:
            None
        """
        patch, index = self._prev_patch(current_patch_num)
        self._activation_callback(patch, index)

    def _next_patch(self, current_patch_num):
        """
        Move to the next patch in the image.

        Args:
            current_patch_num: The index of the current patch.

        Returns:
            (patch, current_patch_index) if there is a next patch
            (None, -1) if there is not a next patch
        """

        patches = self._image.patches

        next_index = current_patch_num + 1

        if next_index < len(patches):
            return patches[next_index], next_index

        else:
            return None, -1


class UndoTool(FGTTool):
    """
    A tool for undoing mistakes.
    """

    def __init__(self, undo_manager, undo_callback):
        """
        Initialize the tool

        Args:
            undo_manager: The manager for undo and redo operations
            undo_callback: A function taking in a patch object and string tag
                           to call when the undo action is taken.
        Returns:
            A tool object
        """
        super(UndoTool, self)\
            .__init__("Undo", undo_icon, 9, undo_manager,
                      "CTRL+Z", cursor='none', persistant=False,
                      activation_callback=undo_callback)

    def on_activate(self, current_patch_num):
        """
        Activate the undo tool.

        Args:
            current_patch_num: The current patch index in the patches list.

        Returns:
            The patch data and operation string.

        Postconditions:
            The last action is undone and put on the redo stack.
        """

        patch, string = self._undo()
        self._activation_callback(patch, string)

    def _undo(self):
        """
        Undo the last operation.


        Returns:
            The patch data and the operation string
        """

        return self.undo_manager.undo()


class RedoTool(FGTTool):
    """
    A tool for redoing undid mistakes.
    """

    def __init__(self, undo_manager, redo_callback):
        """
        Initialize the tool

        Args:
            undo_manager: The manager for undo and redo operations
            redo_callback: A function taking in a patch and string to call
                           when the undo action is taken.
        Returns:
            A tool object
        """
        super(RedoTool, self)\
            .__init__("Redo", redo_icon, 10, undo_manager, "CTRL+R",
                      cursor='none', persistant=False,
                      activation_callback=redo_callback)

    def on_activate(self, current_patch_num):
        """
        Activate the redo tool.

        Args:
            current_patch_num: The current patch index in the patches list.

        Returns:
            The patch data and operation string

        Postconditions:
            The last undone action is redone and put on the undo stack.
        """

        patch, string = self._redo()
        self._activation_callback(patch, string)

    def _redo(self):
        """
        Redo the undone last operation.


        Returns:
            The patch data and the operation string
        """

        return self.undo_manager.redo()
