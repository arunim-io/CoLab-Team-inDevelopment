import { useState } from "react";
import { Control } from "react-hook-form";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import { IconButton, InputAdornment } from "@mui/material";

import BasicTextField from "./BaseTextField";

interface Props {
  name?: string;
  label?: string;
  control: Control;
}

export default function PasswordField({
  name = "password",
  label = "Password",
  ...otherProps
}: Props) {
  const [show, setShow] = useState(false);

  const endAdornment = (
    <InputAdornment position="end">
      <IconButton onClick={() => setShow((show) => !show)}>
        {show ? <VisibilityOff /> : <Visibility />}
      </IconButton>
    </InputAdornment>
  );

  return (
    <BasicTextField
      name={name}
      fieldProps={{
        type: show ? "text" : "password",
        label,
        InputProps: { endAdornment },
      }}
      {...otherProps}
    />
  );
}