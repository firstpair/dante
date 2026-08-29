// Library cover for the public Italian–English edition, rendered by typst to
// cover/dante-commedia-russian-cover.png (8.5in × 11in). The banner is images/dante-header.png.
#set page(width: 8.5in, height: 11in, margin: 0pt, fill: rgb("#16130f"))
#set text(font: "Libertinus Serif", fill: rgb("#efe6d2"))
#set par(leading: 0.3em)
#place(top + left, image("../images/dante-header.png", width: 8.5in))
#place(top + left, dx: 0.85in, dy: 3.4in)[
  #text(size: 17pt, tracking: 0.28em, fill: rgb("#c9a86a"))[DANTE ALIGHIERI]
  #v(0.5in)
  #text(size: 62pt, weight: "medium", fill: rgb("#f4ecdc"))[La Divina \ Commedia]
  #v(0.35in)
  #line(length: 2.2in, stroke: 1.2pt + rgb("#c9a86a"))
  #v(0.3in)
  #text(size: 22pt, style: "italic")[Inferno · Purgatorio · Paradiso]
  #v(0.5in)
  #text(size: 16pt)[The Italian beside the Russian of]
  #v(0.05in)
  #text(size: 24pt)[Dmitry Min]
  #v(0.25in)
  #text(size: 13.5pt, fill: rgb("#bfb39c"))[aligned tercet by tercet, with a learner's dictionary of every word]
]
#place(bottom + left, dx: 0.85in, dy: -0.7in)[
  #text(size: 14pt, tracking: 0.22em, fill: rgb("#c9a86a"))[FIRST PAIR PRESS]
]
