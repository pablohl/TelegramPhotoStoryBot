# output_fun.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, SimpleDocTemplate, Spacer, PageBreak
from reportlab.lib.units import inch

import reportlab.rl_config

reportlab.rl_config.warnOnMissingFontGlyphs = 0

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from constants import PATH_FONT

# Register a nice font
pdfmetrics.registerFont(TTFont("Basker", PATH_FONT + "LibreBaskerville-Regular.ttf"))
pdfmetrics.registerFont(TTFont("BaskerBd", PATH_FONT + "LibreBaskerville-Bold.ttf"))
pdfmetrics.registerFont(TTFont("BaskerIt", PATH_FONT + "LibreBaskerville-Italic.ttf"))
pdfmetrics.registerFont(TTFont("BaskerBI", PATH_FONT + "LibreBaskerville-Bold.ttf"))

from reportlab.lib.styles import ParagraphStyle

from reportlab.pdfbase.pdfmetrics import registerFontFamily

registerFontFamily(
    "Basker", normal="Basker", bold="BaskerBd", italic="BaskerIt", boldItalic="BaskerBI"
)


# Create a function to draw a line
class BoxyLine(Flowable):
    """ """

    # ----------------------------------------------------------------------
    def __init__(self, x=0, y=-15, width=40, height=15, text=""):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    # ----------------------------------------------------------------------
    def draw(self):
        """
        Draw the shape, text, etc
        """
        self.canv.setLineWidth(2)
        self.canv.line(self.x, 0, 455, 0)


from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib import utils
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


def get_image(path, width=1 * cm, **kwargs):
    from reportlab.platypus import Image

    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    is_vertical = iw < ih
    if is_vertical:
        width = 9.5 * cm

    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect), **kwargs), is_vertical


# Generate a PDF with the image and story
def base_to_PDF(imgpath, imgfilename, story, path, namefile):
    doc = SimpleDocTemplate(
        path + namefile + ".pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=36,
        bottomMargin=10,
    )
    styles = getSampleStyleSheet()
    flowables = []
    im, is_v = get_image(imgpath + imgfilename, width=13 * cm, hAlign="CENTER")
    space = Spacer(width=10 * cm, height=0.5 * cm)
    flowables.append(space)
    if is_v == False:
        flowables.append(space)
        flowables.append(space)
    flowables.append(im)
    if is_v == False:
        flowables.append(space)
    flowables.append(space)
    style = getSampleStyleSheet()
    yourStyle = ParagraphStyle(
        "yourtitle",
        fontName="Basker",
        fontSize=18,
        parent=style["Heading2"],
        alignment=4,
        spaceAfter=14,
    )
    story = Paragraph(story, style=yourStyle)
    box = BoxyLine()
    flowables.append(box)
    flowables.append(story)
    flowables.append(box)
    doc.build(flowables)

    return doc
