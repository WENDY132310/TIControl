# =====================================================
# SCRIPT DE INVENTARIO TI - CLIENTE (OPTIMIZADO)
# =====================================================
if ([IntPtr]::Size -ne 8) {
    [System.Windows.Forms.MessageBox]::Show(
        "Este inventario debe ejecutarse en PowerShell 64 bits.",
        "Error de arquitectura",
        "OK",
        "Error"
    )
    exit
}
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$API_URL = "http://192.168.80.125:5000/api"

# =====================================================
# FUNCIONES
# =====================================================

function Show-InputDialog {
    param(
        [string]$Title,
        [string]$Prompt,
        [string[]]$Options = $null,
        [bool]$IsComboBox = $false
    )

    $form = New-Object System.Windows.Forms.Form
    $form.Text = $Title
    $form.Size = New-Object System.Drawing.Size(400, 180)
    $form.StartPosition = 'CenterScreen'
    $form.FormBorderStyle = 'FixedDialog'
    $form.MaximizeBox = $false

    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Prompt
    $label.Location = '10,20'
    $label.Size = '360,20'
    $form.Controls.Add($label)

    if ($IsComboBox) {
        $inputControl = New-Object System.Windows.Forms.ComboBox
        $inputControl.Location = '10,50'
        $inputControl.Size = '360,20'
        $inputControl.DropDownStyle = 'DropDownList'
        foreach ($opt in $Options) { [void]$inputControl.Items.Add($opt) }
        if ($inputControl.Items.Count -gt 0) { $inputControl.SelectedIndex = 0 }
    }
    else {
        $inputControl = New-Object System.Windows.Forms.TextBox
        $inputControl.Location = '10,50'
        $inputControl.Size = '360,20'
    }
    $form.Controls.Add($inputControl)

    $ok = New-Object System.Windows.Forms.Button
    $ok.Text = 'OK'
    $ok.Location = '200,100'
    $ok.DialogResult = 'OK'
    $form.AcceptButton = $ok
    $form.Controls.Add($ok)

    $cancel = New-Object System.Windows.Forms.Button
    $cancel.Text = 'Cancelar'
    $cancel.Location = '290,100'
    $cancel.DialogResult = 'Cancel'
    $form.Controls.Add($cancel)

    if ($form.ShowDialog() -eq 'OK') {
        if ($IsComboBox) { return $inputControl.SelectedItem }
        else { return $inputControl.Text }
    }
    return $null
}

function Send-InventarioData {
    param (
        [hashtable]$Data
    )

    try {
        $json = $Data | ConvertTo-Json -Depth 10
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

        $response = Invoke-RestMethod `
            -Uri "$API_URL/equipos" `
            -Method POST `
            -Body $bytes `
            -Headers @{ "Content-Type" = "application/json; charset=utf-8" } `
            -TimeoutSec 30

        return $response
    }
    catch {
        throw "Error al enviar datos: $_"
    }
}

# =====================================================
# CACHE DE INFORMACIÓN (OPTIMIZACIÓN REAL)
# =====================================================

# TODO lo pesado se consulta UNA SOLA VEZ
$cs = Get-CimInstance Win32_ComputerSystem
$bios = Get-CimInstance Win32_BIOS
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$ram = Get-CimInstance Win32_PhysicalMemory | Select-Object -First 1

$lic = Get-CimInstance `
    -Namespace root/cimv2 `
    -ClassName SoftwareLicensingProduct `
    -ErrorAction SilentlyContinue |
Where-Object { $_.PartialProductKey -and $_.Name -like "*Windows*" } |
Select-Object -First 1


$av = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct `
    -ErrorAction SilentlyContinue | Select-Object -First 1

$physicalDisks = Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue


# =====================================================
# DATOS CALCULADOS (SIN NUEVAS CONSULTAS)
# =====================================================

$pc = $env:COMPUTERNAME

$ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "169.*" -and $_.IPAddress -ne "127.0.0.1" }
).IPAddress -join ", "

$mac = (Get-CimInstance Win32_NetworkAdapterConfiguration -ErrorAction SilentlyContinue |
Where-Object { $_.IPEnabled } |
Select-Object -ExpandProperty MACAddress) -join ", "


$tipoEquipo = "Escritorio"
if ($cs.PCSystemType -eq 2) { $tipoEquipo = "Portátil" }

$ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB)

$ramType = "Desconocida"
switch ($ram.SMBIOSMemoryType) {
    24 { $ramType = "DDR3" }
    26 { $ramType = "DDR4" }
    34 { $ramType = "DDR5" }
}

$diskInfo = ($physicalDisks | ForEach-Object {
        "$($_.FriendlyName) - $([math]::Round($_.Size/1GB)) GB - $($_.MediaType)"
    }) -join " | "

$winLicenseStatus = "No licenciado"
if ($lic.LicenseStatus -eq 1) { $winLicenseStatus = "Licenciado" }

$office = Get-ItemProperty `
    HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* ,
HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* `
    -ErrorAction SilentlyContinue |
Where-Object { $_.DisplayName -like "*Office*" } |
Select-Object -First 1

# =====================================================
# INTERFAZ (IGUAL A LA TUYA)
# =====================================================

$unidadesDisponibles = @(
    "Santa Clara", "San Blas", "Materno Infantil", "Victoria", "Diana Turbay",
    "Chircales", "Olaya", "Altamira", "Alpes", "Cruces", "Primera de mayo",
    "Antonio Nariño", "Perseverancia", "Samper mendoza", "Archivo",
    "Candelaria", "San Cristobal", "Bravo paez", "Bello Horizonte",
    "Laches", "Libertadores", "San Jorge", "Jorge Eliecer",
    "San Jose Obrero", "Calle 34", "Carcel"
)

$unidad = Show-InputDialog "Inventario TI" "Seleccione la unidad:" $unidadesDisponibles $true
$tipoArea = Show-InputDialog "Inventario TI" "Seleccione el tipo de área:" @("Asistencial", "Administrativo") $true
$observaciones = Show-InputDialog "Inventario TI" "Observaciones (opcional):"
if (-not $observaciones) { $observaciones = "Ninguna" }

$Ptorre = Show-InputDialog "Inventario TI" "Placa de Equipo:"
if (-not $Ptorre) { $Ptorre = "No Aplica" }

$Ppantalla = Show-InputDialog "Inventario TI" "Placa de Pantalla:"
if (-not $Ppantalla) { $Ppantalla = "No Aplica" }

# =====================================================
# OBJETO FINAL (MISMO CONTENIDO)
# =====================================================
$datos = @{
    Nombre_Equipo     = $pc
    IP                = $ip
    MAC               = $mac
    Marca             = $cs.Manufacturer
    Modelo            = $cs.Model
    Tipo_Equipo       = $tipoEquipo
    Serial_PC         = $bios.SerialNumber
    Procesador        = $cpu.Name
    RAM_GB            = $ramGB
    Tipo_RAM          = $ramType
    Discos            = $diskInfo
    Sistema_Operativo = $os.Caption
    Arquitectura      = $os.OSArchitecture
    Licencia_Windows  = $winLicenseStatus
    Office            = if ($office) { $office.DisplayName } else { "No instalado" }
    Version_Office    = if ($office) { $office.DisplayVersion } else { "NO APLICA" }
    Antivirus         = if ($av) { $av.displayName } else { "No detectado" }
    Unidad            = $unidad
    Tipo_Area         = $tipoArea
    Observaciones     = $observaciones
    Placa_Equipo      = $Ptorre
    Placa_Pantalla    = $Ppantalla
}

# =====================================================
# ENVÍO
# =====================================================

Send-InventarioData -Data $datos
try {
    Write-Host "Enviando información al servidor..." -ForegroundColor Cyan
    
    $response = Send-InventarioData -Data $datos
    
    Write-Host "✓ Datos enviados exitosamente" -ForegroundColor Green
    
    [System.Windows.Forms.MessageBox]::Show(
        "Inventario registrado exitosamente`n`nEquipo: $pc`nUnidad: $unidad`nAcción: $($response.accion)",
        "Inventario Completado",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    )
}
catch {
    Write-Host "✗ Error al enviar datos" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    [System.Windows.Forms.MessageBox]::Show(
        "Error al enviar el inventario:`n`n$($_.Exception.Message)`n`nVerifique que el servidor esté activo en $API_URL",
        "Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
}

Write-Host "`nPresione cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
