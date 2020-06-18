static
void simple_loop(void)
{
    volatile int i;
    for (i = 0;
         i < 10;
         i++)
    {
    }
}

int main(int argc, char *argv[])
{
    simple_loop();
    return 0;
}
