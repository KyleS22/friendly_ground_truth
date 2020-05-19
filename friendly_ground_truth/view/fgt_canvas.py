"""
File Name: fgt_canvas.py

Authors: Kyle Seienthal

Date: 13-05-2020

Description: Canvas widget for displaying and interacting with images.


Code largely adapted from https://stackoverflow.com/a/48137257
"""
import math
import warnings
import tkinter as tk

from tkinter import ttk
from PIL import Image, ImageTk


class AutoScrollbar(ttk.Scrollbar):
    """
    Self hiding scrollbar.
    """

    def set(self, lo, hi):

        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

        def pack(self, **kw):
            raise tk.TclError('Cannot use pack with the widget ' +
                              self.__class__.__name__)

        def place(self, **kw):
            raise tk.TclError('Cannot use place with the widget ' +
                              self.__class__.__name__)


class FGTCanvas:
    """
    A canvas that allows panning and zooming of large images.

    Attributes:
        imscale: The current scale of the image
        cursor: The current cursor to use on the image
    """

    def __init__(self, placeholder, img, main_window):

        self._previous_position = (0, 0)
        self._coord_scale = 1
        self._dragged = False

        self.imscale = 1.0  # Scale of the image

        self._main_window = main_window

        self.__delta = 1.3  # Zoom magnitude
        self.__filter = Image.ANTIALIAS
        self.__previous_state = 0  # The previous state of the keyboard
        self.__imframe = ttk.Frame(placeholder)

        self.img = img

        # Scrollbars
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')

        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')

        # Create the canvas
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set,
                                yscrollcommand=vbar.set)

        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # Make sure the canvas updates

        hbar.configure(command=self.__scroll_x)
        vbar.configure(command=self.__scroll_y)

        # Bind events to the canvas
        # When the canvas is resized
        self.canvas.bind('<Configure>', lambda event: self.__show_image())
        # Remember the canvas position
        self.canvas.bind('<ButtonPress-1>', self.__move_from)

        self.canvas.bind('<ButtonRelease-1>', self._on_click_release)
        # Move the canvas
        self.canvas.bind('<B1-Motion>', self.__move_to)
        # Zoom for Windows and MacOs
        self.canvas.bind('<MouseWheel>', self.__wheel)
        # Zoom for Linux, scroll down
        self.canvas.bind('<Button-5>', self.__wheel)
        # Zoom for Linux, scroll up
        self.canvas.bind('<Button-4>', self.__wheel)

        # Deal with keystrokes in idle mode
        self.canvas.bind('<Key>', lambda event:
                         self.canvas.after_idle(self.__keystroke, event))

        # Cursor stuff
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Enter>', self._set_cursor)
        self.canvas.bind('<Leave>', self._default_cursor)
        self.canvas.bind('<FocusOut>', self._default_cursor)
        self.canvas.bind('<FocusIn>', self._set_cursor)

        # Decide if the image is too big
        self.__huge = False
        self.__huge_size = 14000
        self.__band_width = 1024

        Image.MAX_IMAGE_PIXELS = 1000000000

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.__image = Image.fromarray(self.img)

        self.imwidth, self.imheight = self.__image.size

        if (self.imwidth * self.imheight > self.__huge_size * self.__huge_size
           and self.__image.tile[0][0] == 'raw'):

            self.__huge = True
            self.__offset = self.__image.tile[0][2]
            self.__tile = [self.__image.tile[0][0],
                           [0, 0, self.imwidth, 0],
                           self.__offset,
                           self.__image.tile[0][3]]

        self.__min_side = min(self.imwidth, self.imheight)

        # Image Pyramid
        if self.__huge:
            self.__pyramid = [self.smaller()]
        else:
            self.__pyramid = [Image.fromarray(self.img)]

        # Set ratio coefficeint for pyramid
        if self.__huge:
            self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size
        else:
            self.__ratio = 1.0

        self.__curr_img = 0  # The current image from the pyramid
        self.__scale = self.imscale * self.__ratio
        self.__reduction = 2  # Reduction degree of pyramid

        w, h, = self.__pyramid[-1].size
        while w > 512 and h > 512:
            w /= self.__reduction
            h /= self.__reduction
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)),
                                  self.__filter))

        # Put image into rectangle for setting corrdinates
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth,
                                                      self.imheight), width=0)
        self._cursor = "arrow"
        self._brush_cursor = None
        self._brush_radius = None

        self.__show_image()
        self.canvas.focus_set()

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, value):
        self._cursor = value

    @property
    def brush_radius(self):
        return self._brush_radius

    @brush_radius.setter
    def brush_radius(self, value):
        self._brush_radius = value
        self.draw_brush()

    def new_image(self, image):
        """
        Reset the image and all properties of the image on the canvas.

        Args:
            image: The image, a numpy array.

        Returns:
            None
        """

        self.canvas.scan_mark(0, 0)
        self.canvas.scan_dragto(0, 0, gain=1)
        self.canvas.scale('all', 0, 0, 1, 1)
        self.imscale = 1.0

        self.canvas.delete("all")
        self.img = image

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.__image = Image.fromarray(self.img)

        self.imwidth, self.imheight = self.__image.size

        if (self.imwidth * self.imheight > self.__huge_size * self.__huge_size
           and self.__image.tile[0][0] == 'raw'):

            self.__huge = True
            self.__offset = self.__image.tile[0][2]
            self.__tile = [self.__image.tile[0][0],
                           [0, 0, self.imwidth, 0],
                           self.__offset,
                           self.__image.tile[0][3]]

        self.__min_side = min(self.imwidth, self.imheight)

        # Image Pyramid
        if self.__huge:
            self.__pyramid = [self.smaller()]
        else:
            self.__pyramid = [Image.fromarray(self.img)]

        # Set ratio coefficeint for pyramid
        if self.__huge:
            self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size
        else:
            self.__ratio = 1.0

        self.__curr_img = 0  # The current image from the pyramid
        self.__scale = self.imscale * self.__ratio
        self.__reduction = 2  # Reduction degree of pyramid

        w, h, = self.__pyramid[-1].size
        while w > 512 and h > 512:
            w /= self.__reduction
            h /= self.__reduction
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)),
                                  self.__filter))

        # Put image into rectangle for setting corrdinates
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth,
                                                      self.imheight), width=0)
        self.__show_image()
        self.canvas.focus_set()

    def _on_motion(self, event):
        """
        Called when the mouse is moved.

        Args:
            event: The mouse event.

        Returns:
            None

        Postconditions:
            The mouse cursor is drawn.
            Previous position is set.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        pos = (x, y)

        if self._cursor == "brush":
            self.draw_brush(pos)

        self._previous_position = pos

    def _set_cursor(self, event):
        """
        Set the cursor to the current specified icon/

        Args:
            event: Event

        Returns:
            None
        """
        if self._cursor == "brush":
            self.canvas.config(cursor="none")
            self.draw_brush()
        else:
            self.canvas.config(cursor=self._cursor)
            if self._brush_cursor is not None:
                self.canvas.delete(self._brush_cursor)

    def _default_cursor(self, event):
        """
        Set the cursor back to the default.

        Args:
            event: The event

        Returns:
            None
        """
        self.canvas.config(cursor="arrow")
        self._previous_position = (50, 50)

    def draw_brush(self, pos=None):
        """
        Draw the paintbrush cursor

        Args:
            pos: The position to draw the brush at.  The default value is None.

        Returns:
            None

        Postcondition:
            The brush is drawn on the canvas/
        """
        if self._brush_cursor is not None:
            self.canvas.delete(self._brush_cursor)

        if self._brush_radius is None:
            self._brush_radius = 15

        if pos is None:
            pos = self._previous_position

        x_max = pos[0] + (self._brush_radius * self._coord_scale)
        x_min = pos[0] - (self._brush_radius * self._coord_scale)
        y_max = pos[1] + (self._brush_radius * self._coord_scale)
        y_min = pos[1] - (self._brush_radius * self._coord_scale)

        self._brush_cursor = self.canvas.create_oval(x_max, y_max, x_min,
                                                     y_min,
                                                     outline='white')

    def set_image(self, img):
        self.img = img
        self.__show_image()
        self.canvas.focus_set()

    def smaller(self):
        """
        Resize the image to be smaller.


        Returns:
            A resized PIL image
        """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)

        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2

        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # Compression ratio
            w = int(w2)  # Band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1
            w = int(w2)
        else:  # aspect_ratio1 < aspect_ratio2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1
            w = int(h2 * aspect_ratio1)

        i, j, _ = 0, 1, round(0.5 + self.imheight / self.__band_width)

        while i < self.imheight:
            # Width of the tile band
            band = min(self.__band_width, self.imheight - i)

            self.__tile[1][3] = band

            # Tile offset (3 bytes per pixel)
            self.__tile[2] = self.__offset + self.imwidth * i * 3
            self.__image.close()
            self.__image = Image.fromarray(self.img)
            self.__image.size = (self.imwidth * band)
            self.__image.tile = [self.__tile]

            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop
            image.paste(cropped.resize((w, int(band * k)+1), self.__filer), (0,
                        int(i * k)))

            i += band
            j += 1

        return image

    def redraw_figures(self):
        """
        Dummy function for redrawing in children classes


        Returns:
            None
        """
        pass

    def grid(self, **kw):
        """
        Put the Canvas widget on the parent widget.

        Args:
            **kw: Kwargs

        Returns:
            None
        """
        self.__imframe.grid(**kw)  # Put the canvas on the grid
        self.__imframe.grid(sticky='nswe')  # Make frame sticky
        self.__imframe.rowconfigure(0, weight=1)  # Make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """
        Cannot use pack.

        Args:
            **kw: Kwargs

        Returns:
            None

        Raises:
            Exception, you can't use the pack function.
        """
        raise Exception('Cannot use pack with the widget ' +
                        self.__class__.__name__)

    def place(self, **kw):
        """
        The place method of the tkinter widget.

        Args:
            **kw: kwargs

        Returns:
            None

        Raises:
            An exception, as this cannot be used with this widget.
        """
        raise Exception('Cannot use place with the widget ' +
                        self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """
        Scroll in the x direction.

        Args:
            *args: args
            **kwargs: kwargs

        Returns:
            None

        Postconditions:
            The canvas is scrolled horizontally.
        """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """
        Scroll in the y direction

        Args:
            *args: args
            **kwargs: kwargs

        Returns:
            None

        Postconditions:
            The canvas is scrolled vertically.
        """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """
        Display the current image


        Returns:
            None

        Postconditions:
            The image is drawn on the canvas.
        """
        if self._cursor == "brush":
            self.draw_brush()
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        # convert to integer or it will not work properly
        box_img_int = tuple(map(int, box_image))  # Get scroll region box

        box_img_width = box_img_int[2] - box_img_int[0]

        xscale = box_img_width/self.img.shape[1]

        self._coord_scale = xscale

        box_scroll = [min(box_img_int[0], box_canvas[0]),
                      min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]),
                      max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll region to tuple and to integer
        # set scroll region
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))

        # get coordinates (x1,y1,x2,y2) of the image tile
        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]

        # show image if it in the visible area
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = (self.__offset + self.imwidth *
                                  int(y1 / self.imscale) * 3)
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                # set size of the tile band
                self.__image.size = (self.imwidth, h)
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0,
                                          int(x2 / self.imscale), h))
            else:  # show normal image
                # crop current img from pyramid
                image = self.__pyramid[max(0, self.__curr_img)].crop(
                                    (int(x1 / self.__scale),
                                     int(y1 / self.__scale),
                                     int(x2 / self.__scale),
                                     int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1),
                                         int(y2 - y1)), self.__filter))

            imageid = self.canvas.create_image(max(box_canvas[0],
                                               box_img_int[0]),
                                               max(box_canvas[1],
                                               box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            # keep an extra reference to prevent garbage-collection
            self.canvas.imagetk = imagetk
            self._image_id = imageid

    def __move_from(self, event):
        """
        Mark the position of the canvas to move from using scanning.

        Args:
            event: The mouse event

        Returns:
            None

        Postconditions:
            The canvas will have a scan mark at the event position.
        """
        if self._cursor != "brush":
            self.canvas.scan_mark(event.x, event.y)

    def _on_click_release(self, event):
        """
        Called when the left mouse button is released.

        Args:
            event: The mouse event.

        Returns:
            None
        """

        if self._dragged:
            self._dragged = False
            return

        pos = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        container_coords = self.canvas.coords(self.container)
        pos = pos[0] - container_coords[0], pos[1] - container_coords[1]
        pos = pos[0] / self._coord_scale, pos[1] / self._coord_scale

        self._main_window.on_canvas_click(pos)

    def __move_to(self, event):
        """
        Move the canvas to the event position.

        Args:
            event: The mouse event.

        Returns:
            None

        Postconditions:
            The canvas is moved to the event position.
        """
        self._dragged = True
        if self._cursor != "brush":

            self.canvas.scan_dragto(event.x, event.y, gain=1)

        if self._cursor == "brush":
            pos = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self._previous_position = pos
            container_coords = self.canvas.coords(self.container)
            pos = pos[0] - container_coords[0], pos[1] - container_coords[1]
            pos = pos[0] / self._coord_scale, pos[1] / self._coord_scale

            self._main_window.on_canvas_drag(pos)
            self.draw_brush(pos)

        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """
        Check it the input point is inside the image area.

        Args:
            x: The x coordinate
            y: The y coordinate

        Returns:
            True if the point is inside the image.
            False if the point is outside the image.
        """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """
        Called when the mouse wheel is scrolled.

        Args:
            event: The mouse event.

        Returns:
            None

        Postconditions:
            The image on the canvas is zoomed.
        """
        # get coordinates of the event on the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y):
            return  # zoom only inside image area

        # Don't scroll if control is down
        if event.state - self.__previous_state == 4:
            return

        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30:
                return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)),
                              len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """
        Called when the keybord is used.

        Args:
            event: The keyboard event.

        Returns:
            None

        Postconditions:
            The canvas is modified according to the key pressed.
        """
        # means that the Control key is pressed
        if event.state - self.__previous_state == 4:
            pass  # do nothing if Control key is pressed
        else:
            # remember the last keystroke state
            self.__previous_state = event.state

    def crop(self, bbox):
        """
        Crop the image using the given bounding box.

        Args:
            bbox: The bounding box, a list

        Returns:
            The cropped image.
        """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            # set offset of the band
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            # set size of the tile band
            self.__image.size = (self.imwidth, band)
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()