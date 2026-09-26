// Пишет story_header.div (объявления встроенных вызовов, событий и запросов Osiris) по
// скомпилированному story.div.osi игры. BG3 не поставляет заголовок, а StoryCompiler без него
// не проверяет сценарии.  Использование: osiheader <story.div.osi> <story_header.div>
using System.Text;
using LSLib.LS.Story;
using LSLib.LS.Story.HeaderParser;

var story = new StoryReader().Read(File.OpenRead(args[0]));
var sb = new StringBuilder();
string TypeName(uint id) => story.Types.TryGetValue(id, out var t) ? t.Name : "UNKNOWN" + id;

// Псевдонимы типов: компилятор требует, чтобы псевдоним указывал на встроенный тип.
foreach (var t in story.Types.Values.OrderBy(t => t.Index))
{
    if (t.IsBuiltin || t.Alias == 0) continue;
    var a = t.Alias;
    while (story.Types.TryGetValue(a, out var at) && at.Alias != 0) a = at.Alias;
    sb.AppendLine($"alias_type {{{t.Name},{t.Index},{a}}}");
}

foreach (var f in story.Functions)
{
    var kw = f.Type switch
    {
        FunctionType.Event => "event",
        FunctionType.Query => "query",
        FunctionType.Call => "call",
        FunctionType.SysQuery => "sysquery",
        FunctionType.SysCall => "syscall",
        _ => null
    };
    if (kw == null) continue; // базы, PROC и QRY из самих сценариев
    var inout = f.Type == FunctionType.Query || f.Type == FunctionType.SysQuery;
    var ps = new List<string>();
    for (var i = 0; i < f.Name.Parameters.Types.Count; i++)
    {
        var tn = TypeName(f.Name.Parameters.Types[i]);
        var isOut = (f.Name.OutParamMask[i >> 3] & (0x80 >> (i & 7))) != 0;
        ps.Add(inout ? $"[{(isOut ? "out" : "in")}]({tn})_Arg{i}" : $"({tn})_Arg{i}");
    }
    sb.AppendLine($"{kw} {f.Name.Name}({string.Join(", ", ps)}) ({f.Meta1},{f.Meta2},{f.Meta3},{f.Meta4})");
}
File.WriteAllText(args[1], sb.ToString());

var parser = new HeaderParser(new HeaderScanner(File.OpenRead(args[1])));
if (!parser.Parse())
{
    Console.Error.WriteLine("Заголовок не разбирается парсером LSLib");
    return 1;
}
Console.WriteLine($"{args[1]}: {parser.GetDeclarations().Functions.Count} функций");
return 0;
