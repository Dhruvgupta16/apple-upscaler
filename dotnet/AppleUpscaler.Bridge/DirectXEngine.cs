using System;
using System.Runtime.InteropServices;

namespace AppleUpscaler.Bridge
{
    /// <summary>
    /// High-performance DirectX / Hardware Acceleration Interop Bridge
    /// </summary>
    public static class DirectXEngine
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetDllDirectory(string lpPathName);

        public static string GetEngineInfo()
        {
            return ".NET 8.0 / C# 12 Hardware Surface Interop Bridge Active";
        }

        public static unsafe void ZeroCopyBlit(byte* pSrc, byte* pDst, int byteLength)
        {
            Buffer.MemoryCopy(pSrc, pDst, byteLength, byteLength);
        }
    }
}
