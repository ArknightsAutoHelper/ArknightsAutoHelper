using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Net.Http;
using System.Buffers;
using System.Runtime.Serialization;
using System.Text.Json.Nodes;
using Tomlyn;
using System.Threading;
using System.Threading.Tasks;
using ICSharpCode.SharpZipLib.Zip;
using System.Diagnostics;

namespace ArknightsAutoHelper
{
    public class Bootstrap
    {
        public static bool HasBootstrapperDirectory { get; private set; } = false;
        public static bool HasPythonExecutable { get; private set; } = false;
        public static bool HasAppPackage { get; private set; } = false;
        public static bool UpdateTriggered { get; set; } = false;
        public static bool NeedBootstrap => UpdateTriggered || !(HasBootstrapperDirectory && HasPythonExecutable && HasAppPackage);

        public static string BootstrapperConfFile { get; } = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "bootstrapper.toml");
        public static string BootstrapperStateDir { get; } = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, ".bootstrapper");
        public static string TriggerUpdateTag { get; } = Path.Combine(BootstrapperStateDir, "trigger_update");
        public static string RuntimeDir { get; } = Path.Combine(BootstrapperStateDir, "runtime");
        public static string PackageStateDir { get; } = Path.Combine(BootstrapperStateDir, "packages");
        public static string UpdatesDir { get; } = Path.Combine(BootstrapperStateDir, "updates");
        public static string CacheDir { get; } = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "cache");

        public class BootstrapperManifest
        {
            public string Version { get; set; }
            public string UpdatePage { get; set; }
            public string DownloadUrl { get; set; }
            public string ReleaseManifestUrl { get; set; }
            [DataMember(Name = "package")]
            public List<PackageDescription> Packages { get; set; }
        }

        public class PackageDescription
        {
            public string Name { get; set; }
            public string Tag { get; set; }
            public string AssetName { get; set; }
            public string DownloadUrl { get; set; }
            public string ExtractBase { get; set; }
        }

        public static event Action<string> StatusText = _ => { };
        public static event Action<long, long> DownloadProgress;
        private static Func<bool> restartCallback = () => true;
        private static HttpClient httpClient;

        public static void SetRestartCallback(Func<bool> callback)
        {
            restartCallback = callback;
        }

        public static void Populate()
        {
            HasBootstrapperDirectory = Directory.Exists(BootstrapperStateDir);
            if (File.Exists(TriggerUpdateTag))
            {
                UpdateTriggered = true;
            }
            HasPythonExecutable = File.Exists(Path.Combine(RuntimeDir, "python3.dll"));
            if (!HasPythonExecutable)
            {
                HasAppPackage = false;
                return;
            }
            var pthfile = Directory.EnumerateFiles(RuntimeDir).FirstOrDefault((x) => x.EndsWith("._pth"));
            if (pthfile != default && File.Exists(pthfile))
            {
                var lines = File.ReadAllLines(pthfile, Encoding.UTF8);
                foreach (var line_ in lines)
                {
                    var line = line_.Trim();
                    if (line.EndsWith(".bin") && File.Exists(Path.Combine(RuntimeDir, line.Trim())))
                    {
                        HasAppPackage = true;
                        break;
                    }
                }
            }
        }

        public static async Task<bool> PerformBootstrapAsync(CancellationToken ct = default)
        {
            var conf = Toml.ToModel(File.ReadAllText(BootstrapperConfFile, Encoding.UTF8));
            var manifest_url = (string)conf["manifest_url"];
            if (manifest_url == null)
            {
                StatusText("ERROR: manifest_url not configured");
                return false;
            }
            StatusText("Checking for updates...");
            httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.TryAddWithoutValidation("User-Agent", "ArknightsAutoHelperBootstrapper");

            var manifest_str = await httpClient.GetStringAsync(manifest_url);
            var table = Toml.ToModel(manifest_str);
            if(new Version((string)table["version"]) > System.Reflection.Assembly.GetEntryAssembly().GetName().Version)
            {
                if (table.ContainsKey("download_url"))
                {
                    // TODO: update bootstrapper
                    await UpdateBootstrapper((string)table["download_url"], ct);
                    // unreachable
                    return true;
                }
                else
                {
                    StatusText("Bootstrapper need update, please visit " + (string)table["update_page"]);
                    return false;
                }
            }
            var manifest = Toml.ToModel<BootstrapperManifest>(manifest_str);
            var releases_bytes = await httpClient.GetByteArrayAsync(manifest.ReleaseManifestUrl);
            var releases = JsonNode.Parse(releases_bytes).AsArray();
            var package2release = releases.Join(
                manifest.Packages,
                release => (string)release["tag_name"],
                package => package.Tag,
                (release, package) => (package, release)
            ).ToDictionary(x => x.package.Name, x => x.release.AsObject());
            var success = true;
            foreach (var package in manifest.Packages)
            {
                StatusText(string.Format("Updating package {0}", package.Name));
                try
                {
                    var result = await UpdatePackage(package, package2release[package.Name], ct);
                    StatusText(string.Format("{0}: {1}", package.Name, result));
                }
                catch (Exception ex)
                {
                    StatusText(string.Format("Failed to update package {0}: {1}", package.Name, ex.Message));
                    success = false;
                }
            }
            if (Directory.Exists(CacheDir))
            {
                StatusText("Purging cache...");
                foreach (var entry in new DirectoryInfo(CacheDir).EnumerateFileSystemInfos())
                {
                    if (entry.Attributes.HasFlag(FileAttributes.Directory))
                    {
                        Directory.Delete(entry.FullName, true);
                    }
                    else
                    {
                        entry.Delete();
                    }
                }
            }
            if (File.Exists(TriggerUpdateTag)) File.Delete(TriggerUpdateTag);
            return success;
        }

        enum PackageUpdateResult
        {
            Success,
            Failed,
            AlreadyUpToDate
        }
        private static async Task<PackageUpdateResult> UpdatePackage(PackageDescription pkg, JsonObject releaseInfo, CancellationToken ct = default)
        {

            DateTime currentTimestamp = default;
            var tsfile = Path.Combine(PackageStateDir, pkg.Name + ".timestamp");
            try
            {
                var ts = File.ReadAllText(tsfile, Encoding.UTF8);
                currentTimestamp = DateTime.Parse(ts, null, System.Globalization.DateTimeStyles.RoundtripKind);
            }
            catch (Exception ex) { }
            var newTimestamp = DateTime.Parse((string)releaseInfo["published_at"], null, System.Globalization.DateTimeStyles.RoundtripKind);
            if (newTimestamp > currentTimestamp)
            {
                var asset = releaseInfo["assets"].AsArray().FirstOrDefault(x => (string)x["name"] == pkg.AssetName);
                if (asset != default)
                {
                    var download_url = (string)asset.AsObject()["browser_download_url"];
                    var download_to = Path.Combine(UpdatesDir, pkg.AssetName);
                    await DownloadAndExtractPackage(download_url, download_to, pkg.ExtractBase, _ => true, ct);
                    Directory.CreateDirectory(PackageStateDir);
                    File.WriteAllBytes(tsfile, Encoding.UTF8.GetBytes(newTimestamp.ToString("o")));
                    return PackageUpdateResult.Success;
                }
                else
                {
                    StatusText(string.Format("No such asset: {0}", pkg.AssetName));
                    return PackageUpdateResult.Failed;
                }
            }
            return PackageUpdateResult.AlreadyUpToDate;
        }

        private static async Task DownloadAndExtractPackage(string download_url, string download_to, string extract_basedir, FastZip.ConfirmOverwriteDelegate confirmOverwrite, CancellationToken ct)
        {
            StatusText(string.Format("Downloading from {0}", download_url));
            Directory.CreateDirectory(UpdatesDir);
            await DownloadFileWithProgress(download_url, download_to, ct);
            StatusText(string.Format("Extracting package {0}", Path.GetFileName(download_to)));
            await Task.Run(() =>
            {
                var fz = new FastZip();
                fz.ExtractZip(download_to, Path.Combine(AppDomain.CurrentDomain.BaseDirectory, extract_basedir), FastZip.Overwrite.Prompt, confirmOverwrite, "", "", true);
                File.Delete(download_to);
            });

        }

        private static async Task DownloadFileWithProgress(string url, string saveTo, CancellationToken ct = default)
        {
            var download_response = await httpClient.GetAsync(url, HttpCompletionOption.ResponseHeadersRead);
            download_response.EnsureSuccessStatusCode();
            var filesize = download_response.Content.Headers.ContentLength.GetValueOrDefault(-1);
            var reprfilesize = filesize > 0 ? FormatSize(filesize) : "unknown size";
            long bytes_transferred = 0;
            DownloadProgress?.Invoke(bytes_transferred, filesize);
            using var download_stream = await download_response.Content.ReadAsStreamAsync();
            using var fs = File.OpenWrite(saveTo);
            var buffer = ArrayPool<byte>.Shared.Rent(81920);
            while (true)
            {
                var len = await download_stream.ReadAsync(buffer, 0, buffer.Length, ct);
                if (len == 0)
                {
                    break;
                }
                bytes_transferred += len;
                await fs.WriteAsync(buffer, 0, len, ct);
                DownloadProgress?.Invoke(bytes_transferred, filesize);
            }
            DownloadProgress?.Invoke(bytes_transferred, filesize);
            DownloadProgress?.Invoke(-1, -1);
            ArrayPool<byte>.Shared.Return(buffer);
        }

        public static string FormatSize(double size)
        {
            if (size < 1024) return string.Format("{0:0} B", size);
            string[] suffixes = { "B", "KiB", "MiB", "GiB", "TiB" };
            int order = 0;
            while (size >= 1024 && order < suffixes.Length - 1)
            {
                order++;
                size = size / 1024;
            }

            return string.Format("{0:0.##} {1}", size, suffixes[order]);
        }

        private static async Task UpdateBootstrapper(string newurl, CancellationToken ct)
        {
            StatusText("Updating bootstrapper...");
            var argv0 = Environment.GetCommandLineArgs()[0];
            var cmdline = Environment.CommandLine;
            if (cmdline[0] == '"')
            {
                cmdline = cmdline.Substring(cmdline.IndexOf('"', 1)+1);
            }
            else
            {
                cmdline = cmdline.Substring(cmdline.IndexOf(' ') + 1);
            }

            await DownloadAndExtractPackage(newurl, Path.Combine(UpdatesDir, "bootstrapper.zip"), ".", file => {
                try
                {
                    using var f = File.Open(file, FileMode.Open, FileAccess.ReadWrite);
                }
                catch
                {
                    var oldfile = Path.Combine(UpdatesDir, Path.GetFileName(file) + ".old");
                    File.Delete(oldfile);
                    File.Move(file, oldfile);
                }
                return true;
            }, ct);
            var wait = restartCallback();
            var p = Process.Start(new ProcessStartInfo(argv0, cmdline) { UseShellExecute = false });
            if (wait)
            {
                p.WaitForExit();
                Environment.Exit(p.ExitCode);
            }
            else
            {
                Environment.Exit(0);
            }
        }
    }
}
