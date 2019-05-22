function Validate() {
  confirmed = confirm('Do you really want to delete?');
  if (confirmed) {
    form.submit();
  }
  else {
    return false;
  }
};
