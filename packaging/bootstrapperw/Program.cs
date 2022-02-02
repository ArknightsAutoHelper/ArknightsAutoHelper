using System;
using System.Windows.Forms;

namespace ArknightsAutoHelper
{
    internal static class GuiBootstrapperProgram
    {
        /// <summary>
        ///  The main entry point for the application.
        /// </summary>
        [STAThread]
        static int Main(string[] args)
        {
            var runApplication = true;
            if (args.Length >= 1 && args[0] == "--update")
            {
                Bootstrap.UpdateTriggered = true;
                runApplication = false;
            }
            Bootstrap.Populate();
            if (Bootstrap.NeedBootstrap)
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                var form = new BootstrapProgressForm();
                Application.Run(form);
                if (form.DialogResult == DialogResult.Cancel)
                {
                    runApplication = false;
                }
            }
            if (runApplication) {
                return Launcher.RunPython(args);
            }
            return 0;
        }
    }
}