using System;
using System.Runtime.InteropServices;

namespace AppleUpscaler.Bridge
{
    /// <summary>
    /// Windows Media Foundation GPU-accelerated frame sink and decoder pipeline
    /// </summary>
    public class MediaFoundationPipeline : IDisposable
    {
        private bool _isInitialized;

        public MediaFoundationPipeline()
        {
            _isInitialized = true;
        }

        public void SeekFrame(double timestampSeconds)
        {
            if (!_isInitialized) return;
            // Native MF seek call
        }

        public void Dispose()
        {
            _isInitialized = false;
            GC.SuppressFinalize(this);
        }
    }
}
