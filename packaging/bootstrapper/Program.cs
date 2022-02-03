using System;
using System.Runtime.InteropServices;
using System.Linq;
using System.IO;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Collections.Concurrent;
using System.Diagnostics;

namespace ArknightsAutoHelper
{
    public class Launcher
    {
        [DllImport("python3", ExactSpelling = true, CharSet = CharSet.Unicode)]
        private static extern int Py_Main(int argc, [MarshalAs(UnmanagedType.LPArray, ArraySubType = UnmanagedType.LPWStr)] string[] argv);

        public static int RunPython(string[] args)
        {
            Environment.SetEnvironmentVariable("AKHELPER_STATE_DIR", AppDomain.CurrentDomain.BaseDirectory);
            var path = Environment.GetEnvironmentVariable("PATH");
            var runtimepath = Bootstrap.RuntimeDir;
            if (!(path.Contains(runtimepath + ";") || path.EndsWith(runtimepath)))
            {
                path = runtimepath + ";" + path;
                Environment.SetEnvironmentVariable("PATH", path);
            }
            var pyargs = new List<string> { "akhelper-launcher" };
            if (!args.Contains("--multiprocessing-fork")) // used by multiprocessing
            {
                var module = Path.GetFileNameWithoutExtension(Environment.GetCommandLineArgs()[0]);
                pyargs.Add("-m");
                pyargs.Add(module);
            }
            pyargs.AddRange(args);
            return Py_Main(pyargs.Count, pyargs.ToArray());
        }

        public static int Main(string[] args)
        {
            Bootstrap.StatusText += output => Console.WriteLine("bootstrapper: {0}", output);
            var runApplication = true;
            if (args.Length >= 1 && args[0] == "--update")
            {
                Bootstrap.UpdateTriggered = true;
                runApplication = false;
            }
            Bootstrap.Populate();
            if (Bootstrap.NeedBootstrap)
            {
                using var q = new BlockingCollection<(long, long)>(new ConcurrentQueue<(long, long)>(), 512);
                using var evt = new System.Threading.AutoResetEvent(false);
                var progressWorker = Task.Run(() =>
                {
                    var sw = new Stopwatch();
                    sw.Start();
                    var lastlen = 0;
                    var last_print = sw.ElapsedMilliseconds;
                    foreach(var (xferd, total) in q.GetConsumingEnumerable())
                    {
                        var clear_last = "\r" + new string(' ', lastlen) + "\r";
                        if (xferd != -1)
                        {
                            if (xferd == 0 || sw.ElapsedMilliseconds - last_print > 500)
                            {
                                var text = string.Format(" {0} / {1}", Bootstrap.FormatSize(xferd), Bootstrap.FormatSize(total));
                                lastlen = text.Length;
                                Console.Write(clear_last + text);
                                last_print = sw.ElapsedMilliseconds;
                            }
                        }
                        else
                        {
                            Console.Write(clear_last);
                            evt.Set();
                            last_print = sw.ElapsedMilliseconds;
                        }
                    }
                });
                Bootstrap.DownloadProgress += (transferred, total) => { 
                    q.Add((transferred, total));
                    if (transferred == -1)
                    {
                        evt.WaitOne();
                    }
                };
                if (!Bootstrap.PerformBootstrapAsync(default).GetAwaiter().GetResult())
                {
                    return 1;
                }
            }
            if (!runApplication) return 0;
            return RunPython(args);
        }
    }
}
