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
/* apply coding highlighting
*/
$('pre').each(function(i, block){
  hljs.highlightBlock(block);
})


/* resize iframes
*/
var $allVideos = $("iframe[src^='https://player.vimeo.com'], iframe[src^='http://player.vimeo.com'], iframe[src^='https://www.youtube.com'], iframe[src^='http://www.youtube.com'], object, embed")
$allVideos.each(function() {
  $(this)
    // jQuery .data does not work on object/embed elements
    .attr('data-aspectRatio', this.height / this.width)
    .removeAttr('height')
    .removeAttr('width');
});

$(window).resize(function() {
  $allVideos.each(function() {
    $fluidEl = $(this).parent();
    var newWidth = $fluidEl.width() * 1.00;
    if ($fluidEl.width() > 600) {
      var newWidth = $fluidEl.width() * 0.60;
    }
    var $el = $(this);
    $el
      .width(newWidth)
      .height(newWidth * $el.attr('data-aspectRatio'));
  });
}).resize();
