document.addEventListener('DOMContentLoaded', function() {
    function generateQrCode() {
        const userId = document.body.dataset.studentId;
        const qrcodeCanvas = document.getElementById("qrcode");
        if (!userId || !qrcodeCanvas) { return; }
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const dateString = `${year}-${month}-${day}`;
        const uniqueData = `${userId},${dateString}`;
        new QRious({
          element: qrcodeCanvas,
          value: uniqueData,
          size: 256,
          padding: 10
        });
    }
    function initialize() {
        if (typeof QRious !== 'undefined') {
            generateQrCode();
        } else {
            setTimeout(initialize, 100); 
        }
    }
    initialize();
});