# HiddenCrypt 

*Deniable Encryption to stop UK police*

#### Stop the Organized Criminal Class.
#### Down with Law Enforcement.
#### Write Code, smash the State.

The 'war on terror' has been a great excuse for statist micro-authoritarian
forces in society. The UK, in particular has led this charge towards tyranny.

The Regulation of Investigatory Powers Act 2000 (RIPA) is an increasingly
used set of regulations used to intimidate activists into handing over
information that can be used by state authorities to blackmail people using
the wide dragnet that is state law, such as the Terrorism Acts 2000 and 2003.

These are not theoretical attacks that could be used at some future date.
They are being used often to intimidate environment activists, hackers and
Kurdish anarchists. There is no presumption of innocence- you are guilty.
Not possessing access to encryption keys is *not* a defence.

HiddenCrypt allows you to bypass RIPA. It creates hidden volumes that forensic
analysis cannot see. You only need a passphrase, and the software will find
the volume and decrypt it. Forensics cannot see the number of hidden volumes
that you have.

Enough is enough. No pasaran! No to destruction of liberty.

#### YES TO ECONOMIC DISOBEDIENCE
#### NO TO CORPORATE STATE SLAVERY
##### YES TO STATE DESTRUCTION
##### NO TO GLOBALIST SUBJUGATION

Requirements:

```sh
  $ sudo apt install cryptsetup python3
```

Create a new hidden volume:

```sh
  $ sudo ./hc.py new
```

Open a new hidden volume:

```sh
  $ sudo ./hc.py open
  $ ls /mnt/
```

Close an opened volume:

```sh
  $ sudo ./hc.py close
```

Technical shit:

Volumes are stored in a single contiguous file (slab) at various offsets.
The offsets are password encrypted and stored in a hashmap array. When you want
to decrypt a store, the password is scrypt hashed, indexed inside the hashmap,
and then the row is decrypted to give the offset of the volume. Then using the
password, the software decrypt the volume.

Currently the software uses LUKS containers but a better system would leave
no container headers so the slab just looks like continuous random data making
forensics harder.

