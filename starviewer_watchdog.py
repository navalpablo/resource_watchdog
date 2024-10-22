import psutil
import time
from datetime import datetime
import csv
import os

def get_starviewer_process():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'starviewer' in proc.info['name'].lower():
            return psutil.Process(proc.info['pid'])
    return None

def format_bytes(bytes):
    """Convert bytes to MB"""
    return f"{bytes / (1024 * 1024):.2f}"

def monitor_starviewer(interval=1, duration=144000):
    start_time = time.time()
    log_file = f"starviewer_monitor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv"
    
    print(f"Starting Starviewer monitoring at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Monitoring for {duration} seconds, checking every {interval} seconds.")
    print(f"Log file: {log_file}")

    with open(log_file, 'w', newline='') as tsvfile:
        # Write explanation at the beginning of the file
        tsvfile.write("Starviewer Monitoring Log\n")
        tsvfile.write(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        tsvfile.write("Interval between measurements: {} seconds\n".format(interval))
        tsvfile.write("Column explanations:\n")
        tsvfile.write("- Timestamp: Date and time of the measurement\n")
        tsvfile.write("- Starviewer_Running: 'Yes' if Starviewer process is detected, 'No' otherwise\n")
        tsvfile.write("- CPU_Usage: Starviewer's CPU usage in percentage\n")
        tsvfile.write("- Memory_Usage: Starviewer's memory usage in MB\n")
        tsvfile.write("- Disk_Read: Cumulative amount of data read by Starviewer in MB\n")
        tsvfile.write("- Disk_Write: Cumulative amount of data written by Starviewer in MB\n")
        tsvfile.write("- System_Disk_Usage: Overall system disk usage in percentage\n")
        tsvfile.write("- System_Memory_Usage: Overall system memory usage in percentage\n")
        tsvfile.write("\n")  # Empty line before the actual data starts

        fieldnames = ['Timestamp', 'Starviewer_Running', 'CPU_Usage_Percent', 'Memory_Usage_MB', 'Disk_Read_MB', 'Disk_Write_MB', 'System_Disk_Usage_Percent', 'System_Memory_Usage_Percent']
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        while time.time() - start_time < duration:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            starviewer = get_starviewer_process()
            log_data = {'Timestamp': timestamp, 'Starviewer_Running': 'No'}

            if starviewer:
                try:
                    with starviewer.oneshot():
                        cpu_percent = starviewer.cpu_percent(interval=1)
                        memory_info = starviewer.memory_info()
                        io_counters = starviewer.io_counters()
                    
                    log_data.update({
                        'Starviewer_Running': 'Yes',
                        'CPU_Usage_Percent': f"{cpu_percent:.2f}",
                        'Memory_Usage_MB': format_bytes(memory_info.rss),
                        'Disk_Read_MB': format_bytes(io_counters.read_bytes),
                        'Disk_Write_MB': format_bytes(io_counters.write_bytes)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    print(f"Starviewer process ended or cannot be accessed at {timestamp}")

            disk = psutil.disk_usage('/')
            memory = psutil.virtual_memory()
            log_data.update({
                'System_Disk_Usage_Percent': f"{disk.percent:.2f}",
                'System_Memory_Usage_Percent': f"{memory.percent:.2f}"
            })

            writer.writerow(log_data)
            tsvfile.flush()  # Ensure data is written to file immediately
            os.fsync(tsvfile.fileno())  # Flush operating system buffers

            time.sleep(interval)

    print(f"Monitoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file saved as: {log_file}")

if __name__ == "__main__":
    try:
        monitor_starviewer()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")