-- Aligned verse for the unified builder. The manuscript marks each tercet as
--   ::: {.tercet data-line="N"}  ::: {.it} line block :::  ::: {.en} line block :::  :::
-- HTML and EPUB keep the divs (book/epub.css lays them out as columns);
-- Typst gets a three-column grid: line number, Italian, English.
if not FORMAT:match('typst') then return {} end

local function cell(div)
  local lines = {}
  for _, block in ipairs(div.content) do
    if block.t == 'LineBlock' then
      for _, line in ipairs(block.content) do
        local text = pandoc.write(pandoc.Pandoc({ pandoc.Para(line) }), 'typst')
        lines[#lines + 1] = text:gsub('%s+$', '')
      end
    else
      lines[#lines + 1] = pandoc.write(pandoc.Pandoc({ block }), 'typst'):gsub('%s+$', '')
    end
  end
  return '[#set par(justify: false, spacing: 0.3em, hanging-indent: 1.4em, first-line-indent: 0pt)\n'
    .. table.concat(lines, '\n\n') .. '\n]'
end

-- Every chapter (a canto, a cantica, the front matter) starts on a new page.
function Header(header)
  if header.level ~= 1 then return nil end
  return { pandoc.RawBlock('typst', '#pagebreak(weak: true)'), header }
end

function Div(div)
  if not div.classes:includes('tercet') then return nil end
  local cells = {}
  for _, child in ipairs(div.content) do
    if child.t == 'Div' then cells[#cells + 1] = cell(child) end
  end
  local number = div.attributes['data-line'] or ''
  local columns = '(2em, 1fr, 1fr)'
  local head = '[#set align(right)\n#text(size: 0.72em, fill: luma(45%))[' .. number .. ']]'
  if #cells == 1 then columns = '(2em, 1fr)' end
  return pandoc.RawBlock('typst',
    '#grid(columns: ' .. columns .. ', column-gutter: 1.3em, ' .. head .. ', ' .. table.concat(cells, ', ') .. ')\n#v(0.55em)\n')
end
