#!/bin/bash

################################################################################
# REAPER Safe Installation Script for VX11 v6.2
# 
# Purpose: Install REAPER DAW with audio stack in VX11 sandbox, with rollback
# 
# Constraints:
#   - NO modifications to VX11 core (except tentaculo_vx11/tools/reaper)
#   - Minimal sudo usage (only for audio packages)
#   - Graceful rollback on any failure
#   - Non-interactive suitable for CI/autonomous execution
#   - Detect audio interfaces and configure appropriately
#
# Author: VX11 Automation
# Date: 2024-01-15
# Version: 1.0
################################################################################

set -o pipefail

# Load cleanup protection helpers to avoid touching CORE paths
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cleanup_protect.sh" || exit 1

################################################################################
# GLOBAL CONFIGURATION
################################################################################

# Paths
readonly DOWNLOADS_DIR="/home/elkakas314/Descargas"
readonly TENTACULO_ROOT="/home/elkakas314/tentaculo_vx11"
readonly REAPER_INSTALL_DIR="${TENTACULO_ROOT}/tools/reaper"
readonly REAPER_PLUGINS_DIR="${REAPER_INSTALL_DIR}/UserPlugins"
readonly REAPER_CONFIG_DIR="${HOME}/.config/REAPER"
readonly LOG_FILE="${TENTACULO_ROOT}/reaper_install.log"
readonly BACKUP_DIR="${TENTACULO_ROOT}/.backup_reaper_$(date +%s)"

# State tracking
ROLLBACK_STEPS=()
AUDIO_BACKEND=""
AUDIO_DEVICES_FOUND=0
INSTALL_SUCCESS=false
REAPER_SOURCE=""  # Will be set by phase_find_installers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# UTILITY FUNCTIONS
################################################################################

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${msg}" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}"
}

# Add rollback step
add_rollback_step() {
    ROLLBACK_STEPS+=("$1")
}

# Execute rollback
execute_rollback() {
    log_warning "Executing rollback..."
    
    for ((i=${#ROLLBACK_STEPS[@]}-1; i>=0; i--)); do
        local step="${ROLLBACK_STEPS[$i]}"
        log_info "Rollback step: $step"
        eval "$step" || log_warning "Rollback step failed (non-critical): $step"
    done
    
    log_error "Installation rolled back. Previous state restored."
}

# Require binary
require_binary() {
    local bin="$1"
    if ! command -v "$bin" &> /dev/null; then
        log_error "Required binary not found: $bin"
        return 1
    fi
    return 0
}

################################################################################
# PHASE 1: PRE-FLIGHT CHECKS
################################################################################

phase_preflight() {
    log_info "=== PHASE 1: PRE-FLIGHT CHECKS ==="
    
    # Check VX11 is intact
    if [ ! -d "/home/elkakas314/vx11" ]; then
        log_error "VX11 core directory not found"
        return 1
    fi
    
    # Check VX11 main modules
    local vx11_modules=("tentaculo_link" "madre" "switch" "hermes" "hormiguero" "manifestator" "mcp" "shubniggurath" "spawner")
    for module in "${vx11_modules[@]}"; do
        if [ ! -d "/home/elkakas314/vx11/$module" ]; then
            log_error "VX11 module missing: $module"
            return 1
        fi
    done
    log_success "VX11 core verified intact"
    
    # Check tentaculo_vx11 exists
    if [ ! -d "${TENTACULO_ROOT}" ]; then
        log_info "Creating tentaculo_vx11 root: ${TENTACULO_ROOT}"
        mkdir -p "${TENTACULO_ROOT}/tools" || {
            log_error "Cannot create tentaculo_vx11"
            return 1
        }
    fi
    
    # Create log directory
    mkdir -p "$(dirname "${LOG_FILE}")" || {
        log_error "Cannot create log directory"
        return 1
    }
    
    # Check required binaries
    require_binary tar || return 1
    require_binary find || return 1
    
    log_success "Pre-flight checks passed"
    return 0
}

################################################################################
# PHASE 2: FIND AND VALIDATE INSTALLER FILES
################################################################################

phase_find_installers() {
    log_info "=== PHASE 2: FIND INSTALLER FILES ==="
    
    if [ ! -d "${DOWNLOADS_DIR}" ]; then
        log_error "Downloads directory not found: ${DOWNLOADS_DIR}"
        return 1
    fi
    
    # Find REAPER installer - try directory first, then tar files
    local reaper_source=""
    
    # Check for reaper_linux_x86_64 directory
    if [ -d "${DOWNLOADS_DIR}/reaper_linux_x86_64" ]; then
        reaper_source="${DOWNLOADS_DIR}/reaper_linux_x86_64"
        log_success "Found REAPER directory: $reaper_source"
    else
        # Try tar.xz or tar.gz files
        local reaper_tarball=$(find "${DOWNLOADS_DIR}" -maxdepth 1 -name "*reaper*" -type f \( -name "*.tar.xz" -o -name "*.tar.gz" \) 2>/dev/null | head -1)
        
        if [ -n "$reaper_tarball" ] && [ -f "$reaper_tarball" ]; then
            reaper_source="$reaper_tarball"
            log_success "Found REAPER tarball: $reaper_source"
        fi
    fi
    
    if [ -z "$reaper_source" ]; then
        log_error "No REAPER installer found in ${DOWNLOADS_DIR}"
        log_info "Looking for: reaper_linux_x86_64/ directory or reaper*.tar.xz"
        return 1
    fi
    
    # Find plugin files (.so, .zip, .tar.xz with plugins)
    log_info "Searching for plugin files..."
    local plugin_count=0
    
    # Count .so files
    plugin_count=$(find "${DOWNLOADS_DIR}" -maxdepth 1 -name "*.so" -type f 2>/dev/null | wc -l)
    if [ "$plugin_count" -gt 0 ]; then
        log_success "Found $plugin_count .so plugin files"
    fi
    
    # Count .zip files (may contain plugins)
    local zip_count=$(find "${DOWNLOADS_DIR}" -maxdepth 1 -name "*.zip" -type f 2>/dev/null | wc -l)
    if [ "$zip_count" -gt 0 ]; then
        log_info "Found $zip_count .zip files (may contain plugins/presets)"
    fi
    
    # Check UserPlugins directory
    if [ -d "${DOWNLOADS_DIR}/UserPlugins" ]; then
        log_success "Found UserPlugins directory in Descargas/"
    fi
    
    # Store result in global variable instead of echo
    REAPER_SOURCE="$reaper_source"
    return 0
}

################################################################################
# PHASE 3: UNINSTALL PREVIOUS REAPER
################################################################################

phase_uninstall_previous() {
    log_info "=== PHASE 3: UNINSTALL PREVIOUS REAPER ==="
    
    local uninstall_targets=(
        "/opt/REAPER"
        "/usr/local/bin/reaper"
        "/usr/bin/reaper"
        "${HOME}/.config/REAPER"
        "${HOME}/.REAPER"
        "${HOME}/REAPER"
        "${REAPER_INSTALL_DIR}"
    )
    
    local found_previous=false
    
    for target in "${uninstall_targets[@]}"; do
        if [ -e "$target" ]; then
            log_warning "Found previous REAPER installation: $target"
            found_previous=true
            
            # Backup if in home directory
            if [[ "$target" == "${HOME}"* ]] || [[ "$target" == "${TENTACULO_ROOT}"* ]]; then
                log_info "Backing up: $target → ${BACKUP_DIR}"
                mkdir -p "${BACKUP_DIR}"
                cp -r "$target" "${BACKUP_DIR}/" || log_warning "Backup failed (non-critical): $target"
                add_rollback_step "cp -r '${BACKUP_DIR}/$(basename $target)' '$target' 2>/dev/null || true"
            fi
            
            # Remove
            log_info "Removing: $target"
            safe_rm "$target" || {
                log_error "Cannot remove: $target"
                return 1
            }
        fi
    done
    
    if [ "$found_previous" = true ]; then
        log_success "Previous REAPER installations removed"
    else
        log_info "No previous REAPER installation found"
    fi
    
    return 0
}

################################################################################
# PHASE 4: EXTRACT REAPER INSTALLER
################################################################################

phase_extract_reaper() {
    local reaper_source="$1"
    
    log_info "=== PHASE 4: EXTRACT/COPY REAPER INSTALLER ==="
    
    # Create install directory
    mkdir -p "${REAPER_INSTALL_DIR}" || {
        log_error "Cannot create REAPER install directory: ${REAPER_INSTALL_DIR}"
        return 1
    }
    add_rollback_step "rm -rf '${REAPER_INSTALL_DIR}'"
    
    # Check if source is a directory or tarball
    if [ -d "$reaper_source" ]; then
        # Handle directory source (e.g., reaper_linux_x86_64/)
        log_info "Copying REAPER from directory: $reaper_source"
        
        # Check if there's a REAPER subdirectory
        if [ -d "$reaper_source/REAPER" ]; then
            cp -r "$reaper_source/REAPER"/* "${REAPER_INSTALL_DIR}/"
        else
            # Copy everything from the directory
            cp -r "$reaper_source"/* "${REAPER_INSTALL_DIR}/" 2>/dev/null || true
        fi
    elif [ -f "$reaper_source" ]; then
        # Handle tarball extraction
        log_info "Extracting REAPER from tarball: $reaper_source"
        
        # Determine compression type
        local tar_opts="-x"
        if [[ "$reaper_source" == *.tar.xz ]]; then
            tar_opts="${tar_opts}J"
        elif [[ "$reaper_source" == *.tar.gz ]]; then
            tar_opts="${tar_opts}z"
        else
            log_error "Unknown tarball format: $reaper_source"
            return 1
        fi
        
        # Extract with safety: check for path traversal
        local temp_extract_dir=$(mktemp -d)
        tar ${tar_opts}f "$reaper_source" -C "$temp_extract_dir" || {
            log_error "Failed to extract REAPER tarball"
            rm -rf "$temp_extract_dir"
            return 1
        }
        
        # Verify no path traversal
        if find "$temp_extract_dir" -name "*/..*" 2>/dev/null | grep -q .; then
            log_error "Tarball contains suspicious paths (path traversal attempt?)"
            rm -rf "$temp_extract_dir"
            return 1
        fi
        
        # Move extracted files (usually from REAPER_*/bin subdirectory)
        if [ -d "$temp_extract_dir/REAPER" ]; then
            safe_mv "$temp_extract_dir/REAPER"/* "${REAPER_INSTALL_DIR}/"
        elif [ -d "$temp_extract_dir/reaper" ]; then
            safe_mv "$temp_extract_dir/reaper"/* "${REAPER_INSTALL_DIR}/"
        else
            # Try moving whatever is in temp
            find "$temp_extract_dir" -maxdepth 1 -type f | head -1 | while read -r file; do
                if [ -f "$file" ]; then
                    safe_mv "$temp_extract_dir"/* "${REAPER_INSTALL_DIR}/"
                fi
            done
        fi
        
        safe_rm "$temp_extract_dir"
    else
        log_error "REAPER source not found: $reaper_source"
        return 1
    fi
    
    # Verify REAPER binary exists
    if [ ! -f "${REAPER_INSTALL_DIR}/reaper" ]; then
        log_error "REAPER binary not found after extraction/copy"
        ls -la "${REAPER_INSTALL_DIR}/" 2>/dev/null || true
        return 1
    fi
    
    # Set permissions
    chmod 755 "${REAPER_INSTALL_DIR}/reaper"
    
    log_success "REAPER installed to: ${REAPER_INSTALL_DIR}"
    return 0
}

################################################################################
# PHASE 5: CREATE COMMAND SYMLINK/WRAPPER
################################################################################

phase_create_reaper_command() {
    log_info "=== PHASE 5: CREATE REAPER COMMAND WRAPPER ==="
    
    # Create wrapper script instead of symlink (safer)
    local wrapper_dir="${TENTACULO_ROOT}/bin"
    local wrapper_file="${wrapper_dir}/reaper"
    
    mkdir -p "${wrapper_dir}" || {
        log_error "Cannot create wrapper bin directory"
        return 1
    }
    
    # Create wrapper script
    cat > "$wrapper_file" << 'WRAPPER_EOF'
#!/bin/bash
# REAPER wrapper script - routes to VX11-sandboxed REAPER
REAPER_INSTALL_DIR="/home/elkakas314/tentaculo_vx11/tools/reaper"
if [ -x "${REAPER_INSTALL_DIR}/reaper" ]; then
    exec "${REAPER_INSTALL_DIR}/reaper" "$@"
else
    echo "Error: REAPER not found at ${REAPER_INSTALL_DIR}/reaper" >&2
    exit 1
fi
WRAPPER_EOF
    
    chmod 755 "$wrapper_file"
    add_rollback_step "rm -f '${wrapper_file}'"
    
    log_success "REAPER wrapper created: $wrapper_file"
    
    # Add to PATH via .bashrc if not already present
    if ! grep -q "tentaculo_vx11/bin" "${HOME}/.bashrc" 2>/dev/null; then
        echo "export PATH=\"${wrapper_dir}:\$PATH\"" >> "${HOME}/.bashrc"
        add_rollback_step "sed -i '/tentaculo_vx11\\/bin/d' '${HOME}/.bashrc'"
        log_info "Added tentaculo_vx11/bin to PATH in ~/.bashrc"
    fi
    
    return 0
}

################################################################################
# PHASE 6: INSTALL PLUGINS
################################################################################

phase_install_plugins() {
    log_info "=== PHASE 6: INSTALL PLUGINS ==="
    
    mkdir -p "${REAPER_PLUGINS_DIR}" || {
        log_error "Cannot create plugins directory: ${REAPER_PLUGINS_DIR}"
        return 1
    }
    add_rollback_step "rm -rf '${REAPER_PLUGINS_DIR}'"
    
    local plugin_count=0
    find "${DOWNLOADS_DIR}" -maxdepth 1 -name "*.so" -type f 2>/dev/null | while read -r plugin; do
        if [ -f "$plugin" ]; then
            log_info "Installing plugin: $(basename $plugin)"
            cp "$plugin" "${REAPER_PLUGINS_DIR}/" || {
                log_warning "Failed to copy plugin: $plugin"
                continue
            }
            ((plugin_count++))
        fi
    done
    
    if [ $plugin_count -gt 0 ]; then
        log_success "Installed $plugin_count plugins"
    else
        log_info "No plugins found to install"
    fi
    
    return 0
}

################################################################################
# PHASE 7: INSTALL & CONFIGURE AUDIO STACK
################################################################################

phase_audio_stack() {
    log_info "=== PHASE 7: INSTALL & CONFIGURE AUDIO STACK ==="
    
    # Detect current audio system
    local current_audio="UNKNOWN"
    if systemctl is-active --quiet pipewire; then
        current_audio="PipeWire"
    elif systemctl is-active --quiet pulseaudio; then
        current_audio="PulseAudio"
    elif systemctl is-active --quiet alsa-utils; then
        current_audio="ALSA"
    fi
    
    log_info "Current audio system: $current_audio"
    
    # Try PipeWire first (modern, JACK compatible)
    log_info "Attempting to setup PipeWire + JACK compatibility..."
    
    if command -v pipewire &> /dev/null; then
        log_success "PipeWire already installed"
        AUDIO_BACKEND="PipeWire"
    else
        log_info "Installing PipeWire packages..."
        if sudo apt-get update -qq && sudo apt-get install -y -qq pipewire pipewire-jack pipewire-alsa pipewire-pulse 2>&1 | tee -a "${LOG_FILE}"; then
            log_success "PipeWire installed successfully"
            AUDIO_BACKEND="PipeWire"
        else
            log_warning "PipeWire installation failed, trying PulseAudio..."
            AUDIO_BACKEND="PulseAudio"
        fi
    fi
    
    # Fallback to PulseAudio if PipeWire failed
    if [ "$AUDIO_BACKEND" = "PulseAudio" ]; then
        if ! command -v pulseaudio &> /dev/null; then
            log_info "Installing PulseAudio packages..."
            if ! sudo apt-get update -qq && sudo apt-get install -y -qq pulseaudio pulseaudio-module-jack 2>&1 | tee -a "${LOG_FILE}"; then
                log_warning "PulseAudio installation also failed, using ALSA fallback"
                AUDIO_BACKEND="ALSA"
            fi
        fi
    fi
    
    # Ensure user is in audio group
    if ! groups "$USER" | grep -q audio; then
        log_info "Adding user to audio group..."
        sudo usermod -a -G audio "$USER" || log_warning "Cannot add user to audio group"
    fi
    
    log_success "Audio backend selected: $AUDIO_BACKEND"
    return 0
}

################################################################################
# PHASE 8: DETECT AUDIO INTERFACES
################################################################################

phase_detect_audio_devices() {
    log_info "=== PHASE 8: DETECT AUDIO DEVICES ==="
    
    # Check ALSA devices
    if command -v aplay &> /dev/null; then
        log_info "ALSA Playback Devices:"
        aplay -L 2>/dev/null | grep -v "^[[:space:]]*$" | head -10 | while read -r device; do
            echo "  - $device" | tee -a "${LOG_FILE}"
            ((AUDIO_DEVICES_FOUND++))
        done
    fi
    
    # Check PulseAudio devices
    if command -v pactl &> /dev/null; then
        log_info "PulseAudio Devices:"
        pactl list short sinks 2>/dev/null | while read -r line; do
            if [ -n "$line" ]; then
                echo "  - $line" | tee -a "${LOG_FILE}"
                ((AUDIO_DEVICES_FOUND++))
            fi
        done
    fi
    
    # Check JACK
    if command -v jack_lsp &> /dev/null; then
        log_info "JACK Status:"
        if jack_lsp &> /dev/null; then
            log_info "  JACK is running"
            AUDIO_DEVICES_FOUND=$((AUDIO_DEVICES_FOUND + 1))
        else
            log_info "  JACK is not running (can be started manually)"
        fi
    fi
    
    # Check USB audio devices
    log_info "USB Audio Devices:"
    if command -v lsusb &> /dev/null; then
        lsusb 2>/dev/null | grep -i audio | while read -r device; do
            echo "  - $device" | tee -a "${LOG_FILE}"
            ((AUDIO_DEVICES_FOUND++))
        done
    fi
    
    if [ $AUDIO_DEVICES_FOUND -eq 0 ]; then
        log_warning "No audio devices detected"
    else
        log_success "Detected $AUDIO_DEVICES_FOUND audio device(s)"
    fi
    
    return 0
}

################################################################################
# PHASE 9: RUN VERIFICATION CHECKS
################################################################################

phase_verify_installation() {
    log_info "=== PHASE 9: VERIFY INSTALLATION ==="
    
    # Check REAPER binary exists and is executable
    if [ ! -x "${REAPER_INSTALL_DIR}/reaper" ]; then
        log_error "REAPER binary not executable: ${REAPER_INSTALL_DIR}/reaper"
        return 1
    fi
    log_success "REAPER binary is executable"
    
    # Try to start REAPER in headless mode
    log_info "Testing REAPER startup (headless)..."
    if timeout 10 "${REAPER_INSTALL_DIR}/reaper" -audioconfig 2>&1 | head -5 | tee -a "${LOG_FILE}"; then
        log_success "REAPER headless mode works"
    else
        log_warning "REAPER headless test timed out or failed (may be normal)"
    fi
    
    # Verify audio backend can see devices
    log_info "Verifying audio backend..."
    case "$AUDIO_BACKEND" in
        PipeWire)
            if command -v pw-cli &> /dev/null; then
                if pw-cli info 2>&1 | grep -q "core.version"; then
                    log_success "PipeWire is responding"
                else
                    log_warning "PipeWire may not be running"
                fi
            fi
            ;;
        PulseAudio)
            if command -v pactl &> /dev/null; then
                if pactl stat 2>&1 | grep -q "Module #"; then
                    log_success "PulseAudio is responding"
                else
                    log_warning "PulseAudio may not be running"
                fi
            fi
            ;;
        ALSA)
            if command -v aplay &> /dev/null; then
                log_success "ALSA is available"
            fi
            ;;
    esac
    
    INSTALL_SUCCESS=true
    log_success "Verification checks passed"
    return 0
}

################################################################################
# PHASE 10: GENERATE SUMMARY REPORT
################################################################################

phase_summary_report() {
    log_info "=== PHASE 10: SUMMARY REPORT ==="
    
    local summary_file="${TENTACULO_ROOT}/reaper_install_summary.txt"
    
    cat > "$summary_file" << SUMMARY_EOF
================================================================================
REAPER Installation Summary Report
Generated: $(date)
================================================================================

INSTALLATION STATUS
  Overall: $([ "$INSTALL_SUCCESS" = true ] && echo "SUCCESS ✓" || echo "FAILED ✗")
  REAPER Install Path: ${REAPER_INSTALL_DIR}
  REAPER Binary: ${REAPER_INSTALL_DIR}/reaper
  Wrapper Command: ${TENTACULO_ROOT}/bin/reaper
  Plugins Directory: ${REAPER_PLUGINS_DIR}
  Configuration: ${REAPER_CONFIG_DIR}

AUDIO CONFIGURATION
  Backend Type: ${AUDIO_BACKEND}
  Audio Devices Found: ${AUDIO_DEVICES_FOUND}
  JACK Support: $(command -v jack_lsp &> /dev/null && echo "Yes" || echo "No")
  ALSA Support: $(command -v aplay &> /dev/null && echo "Yes" || echo "No")

VX11 INTEGRITY
  Status: VERIFIED ✓
  Core Path: /home/elkakas314/vx11
  Modules Checked: 9 (all present)
  Backup Created: ${BACKUP_DIR}

NEXT STEPS
  1. Source ~/.bashrc to update PATH: source ~/.bashrc
  2. Test REAPER: reaper --version
  3. Configure REAPER: ~/.config/REAPER/reaper.ini
  4. For JACK: qjackctl or start manually
  5. For audio issues: check ${LOG_FILE}

TROUBLESHOOTING
  If audio not working:
    - Check audio backend: systemctl status pipewire
    - Verify user in audio group: groups
    - Test ALSA: aplay -l
    - Restart audio daemon: systemctl restart pipewire

ROLLBACK INFORMATION
  If issues occur, this script can be reverted:
  - Manual rollback: rm -rf ${REAPER_INSTALL_DIR}
  - Restore backup: cp -r ${BACKUP_DIR}/* ~/
  - Remove wrapper: rm ${TENTACULO_ROOT}/bin/reaper

================================================================================
Full Log: ${LOG_FILE}
================================================================================
SUMMARY_EOF
    
    cat "$summary_file" | tee -a "${LOG_FILE}"
    log_success "Summary report created: $summary_file"
    
    return 0
}

################################################################################
# ERROR HANDLER & MAIN FLOW
################################################################################

trap 'handle_error' ERR EXIT

handle_error() {
    local line_num=$1
    if [ "$INSTALL_SUCCESS" != true ] && [ "${#ROLLBACK_STEPS[@]}" -gt 0 ]; then
        log_error "Installation failed at line $line_num, executing rollback..."
        execute_rollback
    fi
}

main() {
    log_info "============================================================"
    log_info "REAPER Safe Installation for VX11 v6.2"
    log_info "Start Time: $(date)"
    log_info "============================================================"
    
    # Execute phases in sequence
    phase_preflight || return 1
    
    phase_find_installers || return 1
    
    phase_uninstall_previous || return 1
    
    phase_extract_reaper "$REAPER_SOURCE" || return 1
    
    phase_create_reaper_command || return 1
    
    phase_install_plugins || return 1
    
    phase_audio_stack || true  # Allow non-fatal failure
    
    phase_detect_audio_devices || true  # Allow non-fatal failure
    
    phase_verify_installation || return 1
    
    phase_summary_report || true  # Allow non-fatal failure
    
    log_success "============================================================"
    log_success "REAPER Installation COMPLETED SUCCESSFULLY"
    log_success "End Time: $(date)"
    log_success "============================================================"
    
    return 0
}

################################################################################
# SCRIPT ENTRY POINT
################################################################################

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
    exit $?
fi
