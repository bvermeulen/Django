function validateDelete(objectName) {
  confirmed = confirm('Do you really want to delete ' + objectName + '?');
  if (confirmed) {
    form.submit();
  }
  else {
    return false;
  }
}
