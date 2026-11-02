```
$p='C:\ここを\出力した.xlsx'
Add-Type -A System.IO.Compression.FileSystem
$z=[IO.Compression.ZipFile]::OpenRead($p)
function ReadEntry($n){$r=New-Object IO.StreamReader($z.GetEntry($n).Open(),[Text.Encoding]::UTF8);$t=$r.ReadToEnd();$r.Close();$t}
$sheet=ReadEntry 'xl/worksheets/sheet1.xml';$draw=ReadEntry 'xl/drawings/drawing1.xml';$z.Dispose()
[regex]::Matches($draw,'<xdr:twoCellAnchor.*?</xdr:twoCellAnchor>')|ForEach-Object{$m=[regex]::Matches($_.Value,'<xdr:row>(\d+)</xdr:row><xdr:rowOff>(\d+)<');$n=[int]$m[0].Groups[1].Value+1;$h=[regex]::Match($sheet,"<row r=`"$n`"[^>]*>").Value;"row=$n top=$([int]$m[0].Groups[2].Value/9525)px bottom=$([int]$m[1].Groups[2].Value/9525)px $([regex]::Match($h,'ht="[^"]*"').Value) $([regex]::Match($h,'customHeight="[^"]*"').Value)"}
```
