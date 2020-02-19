/* Material Design for Bootstrap
   https://mdbootstrap.com/
   https://mdbootstrap.com/docs/jquery/tables/scroll/
*/
$(document).ready(function () {
  $('#dtHorizontalVerticalScroll').DataTable({
    "scrollX": true,
    "scrollY": "50vh",
    "scrollCollapse": true,
    "paging": false,
    "ordering": false,
    "searching": false,
    "info": false,
  });
  $('.dataTables_length').addClass('bs-select');
});
