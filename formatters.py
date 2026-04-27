_NAME_MAX_BYTES = 30


def _format_button_text(result: dict) -> str:
    name = result.get('name', '')
    seeds = result.get('seeds', '?')
    size = result.get('size', '?')
    name_bytes = name.encode('utf-8')
    if len(name_bytes) > _NAME_MAX_BYTES:
        name = name_bytes[:_NAME_MAX_BYTES - 3].decode('utf-8', errors='ignore') + '…'
    return f'{name} · {seeds}s · {size}'


def _format_size(size_bytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _state_label(state: str) -> str:
    return {
        'downloading': '⬇️ Downloading',
        'forcedDL':    '⬇️ Downloading',
        'stalledDL':   '⏸ Stalled',
        'queuedDL':    '🕐 Queued',
        'metaDL':      '🔍 Fetching metadata',
        'checkingDL':  '🔍 Checking',
        'checkingUP':  '🔍 Checking',
        'pausedDL':    '⏸ Paused',
        'seeding':     '✅ Done',
        'stalledUP':   '✅ Done',
        'uploading':   '✅ Done',
        'forcedUP':    '✅ Done',
        'pausedUP':    '✅ Done',
    }.get(state, f'❓ {state}')
