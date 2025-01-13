resource "aws_iam_role" "glue_role" {
  name               = "${var.project}-glue-extract-role"
  assume_role_policy = var.glue_assume_role_policy
}

resource "aws_iam_role_policy" "task_role_policy" {
  name   = "${var.project}-glue-role-policy"
  role   = aws_iam_role.glue_role.id
  policy = var.glue_access_policy
}
