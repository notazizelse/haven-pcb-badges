from PIL import Image, ImageDraw, ImageFont
import design as d
F=lambda s: ImageFont.truetype('fonts/Jua-Regular.ttf', s)
H=lambda s: ImageFont.truetype('fonts/DarumadropOne-Regular.ttf', s)
def sheet(names, labels, title, fn, scale=0.42):
    ims=[Image.open(f'mock/{n}.png') for n in names]
    ims=[im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS) for im in ims]
    w,h=ims[0].size; cols=len(ims); top=110
    c=Image.new('RGBA',(w*cols+80, top+h+90),(251,243,228,255))
    dr=ImageDraw.Draw(c)
    dr.text((40,40),title,font=H(46),fill=d.UMBER)
    for i,(im,l) in enumerate(zip(ims,labels)):
        x=40+i*w; y=top
        c.alpha_composite(im,(x,y))
        dr.text((x+w//2,y+h+18),l,font=F(30),fill=d.UMBER,anchor='mt')
    c.convert('RGB').save(fn, quality=92); print(fn,c.size)
sheet(['participant-front','organizer-front'],['Participant (HACKER), front','Organizer, front'],'Haven Tashkent PCB badges','mock/sheet-fronts.png')
sheet(['participant-back','participant-back-pinned','organizer-back'],['Participant back, before the pin','With the bar pin glued on','Organizer back'],'The back: pin zone + message','mock/sheet-backs.png')
sheet(['planB-participant-front','planB-organizer-front'],['Plan B participant: orange mask','Plan B organizer: black mask'],'Plan B: if colour printing is not available','mock/sheet-planB.png')
