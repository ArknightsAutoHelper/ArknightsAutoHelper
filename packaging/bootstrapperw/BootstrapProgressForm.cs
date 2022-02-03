using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ArknightsAutoHelper
{
    public partial class BootstrapProgressForm : Form
    {
        public BootstrapProgressForm()
        {
            InitializeComponent();
            try
            {
                this.Icon = Icon.ExtractAssociatedIcon(Assembly.GetEntryAssembly().Location);
            }
            catch (Exception) { }
            this.Font = SystemFonts.MessageBoxFont;
            DialogResult = DialogResult.None;
        }

        class ProgressOutput
        {
            public string Output { get; set; }
        }
        class ProgressDownload
        {
            public long Transferred { get; set; }
            public long Total { get; set; }
        }
        class ProgressClose { }

        private Stopwatch sw;
        private Progress<object> bootstrapProgress;
        private CancellationTokenSource cts;
        private void HandleProgress(object x)
        {
            if (x is ProgressOutput o)
            {
                outputBox.AppendText(o.Output);
                outputBox.AppendText("\r\n");
            }
            else if (x is ProgressDownload dl)
            {
                if (dl.Transferred != -1)
                {
                    if (dl.Transferred == 0 || sw.Elapsed > TimeSpan.FromMilliseconds(250))
                    {
                        var text = string.Format("{0} / {1}", Bootstrap.FormatSize(dl.Transferred), Bootstrap.FormatSize(dl.Total));
                        downloadProgressLabel.Text = text;
                        if (dl.Total > 0)
                        {
                            progressBar.Style = ProgressBarStyle.Continuous;
                            progressBar.Value = (int)Math.Floor((double)dl.Transferred / dl.Total * progressBar.Maximum);
                        }
                        else
                        {
                            progressBar.Style = ProgressBarStyle.Marquee;
                        }
                        sw.Restart();
                    }
                }
                else
                {
                    progressBar.Style = ProgressBarStyle.Marquee;
                    downloadProgressLabel.Text = "";
                    sw.Restart();
                }
            }
            else if (x is ProgressClose)
            {
                Close();
            }
        }
        
        private async void BootstrapProgressForm_Shown(object sender, EventArgs e)
        {
            bootstrapProgress = new(HandleProgress);
            sw = new();
            cts = new();
            var progress = (IProgress<object>)bootstrapProgress;
            Bootstrap.SetRestartCallback(() =>
            {
                progress.Report(new ProgressClose());
                Application.DoEvents();
                return false;
            });
            Bootstrap.StatusText += s => progress.Report(new ProgressOutput { Output = s });
            Bootstrap.DownloadProgress += (xferd, total) => progress.Report(new ProgressDownload { Transferred = xferd, Total = total });
            try
            {
                var bootstrapresult = await Bootstrap.PerformBootstrapAsync(cts.Token);
                progressBar.Style = ProgressBarStyle.Continuous;
                progressBar.Value = progressBar.Maximum;
                RenameCancel();
                if (bootstrapresult)
                {
                    DialogResult = DialogResult.OK;
                    await Task.Delay(3000);
                    
                    Close();
                }
            }
            catch (Exception ex)
            {
                DialogResult = DialogResult.Cancel;
                progressBar.Style = ProgressBarStyle.Continuous;
                progressBar.Value = progressBar.Minimum;
                outputBox.AppendText(ex.ToString());
                outputBox.AppendText("\r\n");
                outputBox.ForeColor = Color.Red;
                RenameCancel();
            }

        }

        private void RenameCancel()
        {
            cancelButton.Text = "&Close";
            AcceptButton = cancelButton;
            ActiveControl = cancelButton;
        }

        private void cancelButton_Click(object sender, EventArgs e)
        {
            if (DialogResult != DialogResult.OK)
            {
                cts.Cancel();
                DialogResult = DialogResult.Cancel;
            }
            Close();
        }
    }
}
