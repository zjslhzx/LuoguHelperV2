$ErrorActionPreference = "Continue"
Write-Host "=== 步骤1: 查找洛谷窗口 ==="
$proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*洛谷*" } | Select-Object -First 1
if ($proc) {
  Write-Host ("找到进程: " + $proc.ProcessName + " ID=" + $proc.Id)
  Write-Host ("窗口标题: " + $proc.MainWindowTitle)
  Write-Host "=== 步骤2: 激活到前台 ==="
  Add-Type @"
using System; using System.Runtime.InteropServices;
public class W32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
}
""@
  $h = $proc.MainWindowHandle
  [W32]::ShowWindow($h, 9) | Out-Null
  [W32]::SetForegroundWindow($h) | Out-Null
  Start-Sleep -Milliseconds 2000
  Write-Host "已激活，等待2秒..."
} else {
  Write-Host "未找到洛谷窗口"
}
Write-Host "=== 步骤3: 截图（新方式） ==="
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
Write-Host ("屏幕: " + $s.Width + "x" + $s.Height)
try {
  $bmp = New-Object System.Drawing.Bitmap($s.Width, $s.Height)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen([System.Drawing.Point]::Empty, [System.Drawing.Point]::Empty, $s.Size)
  # 用MemoryStream转byte[]再写文件，绕过GDI+路径问题
  $ms = New-Object System.IO.MemoryStream
  $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
  $bytes = $ms.ToArray()
  $ms.Close()
  $g.Dispose()
  $bmp.Dispose()
  $out1 = Join-Path $env:TEMP "luogu_snap1.png"
  [System.IO.File]::WriteAllBytes($out1, $bytes)
  Write-Host ("成功保存1: " + $out1 + " (大小=" + $bytes.Length + "字节)")
  # 再尝试另存到D:\TRAE\
  $out2 = "D:\TRAE\luogu_snap2.png"
  [System.IO.File]::WriteAllBytes($out2, $bytes)
  Write-Host ("成功保存2: " + $out2 + " (大小=" + $bytes.Length + "字节)")
} catch {
  Write-Host ("截图失败: " + $_.Exception.Message)
  Write-Host $_.ScriptStackTrace
}