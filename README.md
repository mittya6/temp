```
$p='C:\ここを\出力した.xlsx'
Add-Type -A System.IO.Compression.FileSystem
$fSheet='xl/worksheets/sheet1.xml';$fBook='xl/workbook.xml';$fStyle='xl/styles.xml'
$views={param($f,$x) if($f -eq $fBook){$x -replace '<sheets>','<bookViews><workbookView/></bookViews><sheets>'}elseif($f -eq $fSheet){$x -replace '<sheetFormatPr','<sheetViews><sheetView workbookViewId="0"/></sheetViews><sheetFormatPr'}else{$x}}
$dy={param($f,$x) if($f -eq $fSheet){$x -replace ' x14ac:dyDescent="[^"]*"',''}else{$x}}
$ver={param($f,$x) if($f -eq $fBook){$x -replace '<fileVersion[^>]*/>','' -replace ' defaultThemeVersion="[^"]*"','' -replace '<calcPr[^>]*/>',''}else{$x}}
$font={param($f,$x) if($f -eq $fStyle){([regex]'<scheme val="minor"/>').Replace(([regex]'<name val="Calibri"/>').Replace($x,'<name val="Yu Gothic"/>',1),'',1)}else{$x}}
$draw={param($f,$x) if($f -eq $fSheet){$x -replace '<drawing [^>]*/>',''}else{$x}}
$page={param($f,$x) if($f -eq $fSheet){$x -replace '<pageSetup[^>]*/>',''}else{$x}}
$list=[ordered]@{A_views=@($views);B_dyDescent=@($dy);C_version=@($ver);D_font=@($font);E_drawing=@($draw);F_pageSetup=@($page);G_all=@($views,$dy,$ver,$font,$draw,$page)}
foreach($k in $list.Keys){
  $o=$p -replace '\.xlsx$',"_$k.xlsx";Copy-Item $p $o -Force
  $z=[IO.Compression.ZipFile]::Open($o,'Update')
  foreach($n in $fSheet,$fBook,$fStyle){
    $e=$z.GetEntry($n);$rd=New-Object IO.StreamReader($e.Open(),[Text.Encoding]::UTF8);$x=$rd.ReadToEnd();$rd.Close();$e.Delete()
    foreach($fn in $list[$k]){$x=& $fn $n $x}
    $wr=New-Object IO.StreamWriter($z.CreateEntry($n).Open(),(New-Object Text.UTF8Encoding($false)));$wr.Write($x);$wr.Close()
  }
  $z.Dispose();"作成: $o"
}
```
